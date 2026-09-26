# Decisions & trade-offs

A short record of the design choices behind this build and why they were made.

## 1. Customer problem, scoped narrowly
**Decision:** Daiichi Sankyo oncology Medical Affairs — MSL next-best-engagement for
Enhertu/Datroway KOLs, not "improve pharma engagement."
**Why:** A specific, real industry problem (siloed MSL signals → missed follow-ups, slow
inquiry SLAs, under-served KOLs) is measurable and demoable. The whole build ladders up to
one KPI set: priority-KOL reach, inquiry SLA, MSL productivity.

## 2. Lakeflow declarative pipeline (SQL, serverless) for the medallion
**Decision:** One serverless Lakeflow pipeline: Volume → Bronze (Auto Loader
`read_files` STREAM) → Silver (clean + `ai_query`) → Gold (materialized views).
**Trade-off:** SQL over Python — the transformations are set-based (joins, window
functions, aggregations), so SQL is the most legible and the least code. Python would only
help for external calls, and `ai_query` is available natively in SQL. Materialized views
for Silver/Gold (not streaming tables) because the analytics are full recomputes over small
synthetic data and one of them (`ai_query`) is non-deterministic — MVs give a clean,
reproducible full refresh.
**Alternative rejected:** hand-run notebooks (what the original demo did). That is not an
integrated pipeline and fails the "show the journey, integrated" bar.

## 3. Gen AI via `ai_query` inside the pipeline, not a separate step
**Decision:** The LLM extraction (`silver_msl_extracted`) runs as a materialized view in
the same pipeline DAG.
**Why:** Keeps the journey integrated — unstructured notes become governed structured
signals in the same lineage graph, no orchestration glue. One LLM call per note (500),
Llama 3.3 70B, JSON-constrained prompt + `from_json` parse + `coalesce` defaults so a
single malformed response can't break the row.
**Trade-off:** Re-runs re-invoke the model. Acceptable at this volume; for production we'd
cache by note hash or only score new/changed notes (CDF).

## 4. Lakebase for operational serving (the gap in the original demo)
**Decision:** Reverse-ETL the Gold `serving_msl_action_queue` into a Lakebase PostgreSQL
synced table (`SNAPSHOT`), plus a transactional write-back table `msl_review_actions`.
**Why:** Delta is great for analytics scans but not for an interactive cockpit that needs
millisecond point lookups and transactional writes of MSL review decisions. Lakebase gives
OLTP serving while UC keeps one governance plane (the synced table is a UC object too).
**Trade-off:** `SNAPSHOT` sync (not CONTINUOUS) — the queue refreshes on demand rather than
in real time. For a daily MSL planning workflow that is the right cost/latency point;
CONTINUOUS (requires CDF) is a one-line change if near-real-time is needed.

## 5. Genie over gold tables + governed metric views
**Decision:** Point Genie at the gold tables and the two metric views, with curated sample
questions.
**Why:** Metric views give Genie governed measure definitions (one definition of "reach",
"engagement score"), so NL answers match the dashboard and app. Verified with a live
question that produced correct SQL + a natural-language answer.

## 6. App = thin, governed UI over proven backends
**Decision:** Streamlit app with two tabs — Lakebase-served action queue, and HCP
pre-engagement (360 + `ai_query` briefing + governed content + Lakebase write-back). Runs
as a service principal with least-privilege grants.
**Why:** The app composes the exact governed objects already built; no business logic hidden
in the app. Every recommendation is explainable from the evidence panels and requires MSL
review — important in a non-promotional Medical Affairs context.

## 7. Governance is enforced, not decorative
**Observation:** The workspace enforces UC **tag policies** (only approved values for
`domain`, `data_classification`, `sensitivity`, etc.). Tags were chosen to comply
(`domain=clinical`, `data_classification=internal`, `npi → sensitivity=pii`). The `npi`
column is classified PII even though synthetic — modelling the real control.

## 8. AI as a force multiplier (how this was built)
Built with Claude (Isaac) driving the Databricks MCP tools and CLI end-to-end: synthetic
data generation, Volume upload, pipeline authoring/creation/run, metric views, Lakebase
provisioning + reverse ETL + write-back, Genie creation and testing, app deployment, and
this documentation. Notable debugging done live: metric-view YAML can't use backticks in
`source:`; `psycopg[binary]` SIGABRTs under Spark serverless (switched to pure-Python
`pg8000` for setup jobs, kept `psycopg` for the app runtime); the serverless SDK needed
pinning to `databricks-sdk>=0.81.0` for the `w.database` API.

## Known limitations
- Synthetic data is internally consistent but simple (templated MSL notes); real notes
  would exercise the extraction harder.
- `SNAPSHOT` Lakebase sync is manual-refresh; wire a job trigger or CONTINUOUS for freshness.
- The AI/BI dashboard (`dashboard/medical_omnichannel_intelligence.lvdash.json`, published —
  see evidence/10) is built on the same governed gold tables as Genie and the app.
