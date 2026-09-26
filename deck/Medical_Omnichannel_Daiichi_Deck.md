% Medical Omnichannel Intelligence — Daiichi Sankyo
% Databricks FE BAR · Medical Affairs (oncology) · synthetic, non-promotional demo

---

# The business problem

**Daiichi Sankyo's oncology franchise (Enhertu, Datroway) is won through scientific
exchange between MSLs and oncology KOLs.**

Today that exchange is **flying blind**:

- MSL field notes, medical inquiries, congress activity and digital engagement live in
  **separate systems**.
- MSLs can't see **which KOLs to prioritize**, **what topics** they care about, or **what
  questions are unanswered**.
- Result: **missed follow-ups, slow medical-inquiry responses, and high-influence KOLs
  left under-served** during critical launch windows.

---

# The outcome we deliver

A governed platform that unifies every engagement signal and turns it into a
**prioritized, AI-assisted next-best-engagement workflow** in an MSL cockpit.

**Estimated ~$3.4M / year** for a 120-MSL field-medical org:

| Lever | Estimated annual value |
|------|------:|
| MSL prep time saved (AI pre-engagement briefings, ~2 h/MSL/week) | ~$1.3M |
| Faster medical-inquiry resolution (overdue surfacing + SLA analytics) | ~$0.6M |
| Priority-KOL reach uplift (90-day reach ~44% → 60%) | ~$1.5M |

- **Executive sponsor (VP Medical Affairs):** higher scientific share-of-voice with
  priority KOLs; defensible inquiry-SLA governance.
- **Domain owner (Field Medical Director):** every MSL walks in prepared, compliant, and
  pointed at the highest-need KOLs first.

---

# What the MSL sees

**Medical Engagement Copilot** (deployed Databricks App):

1. **MSL Action Queue** — KOLs ranked by a priority score (influence × educational need ×
   engagement gap), each with a trigger ("open medical inquiry overdue"), a topic, and a
   recommended date. Served in milliseconds from **Lakebase**.
2. **Pre-Engagement Briefing** — a click generates a grounded, non-promotional AI briefing
   for the selected KOL, plus their 360 (interests, inquiries, congress, publications) and a
   **medically-approved** content recommendation (with review ID).
3. **Write-back** — the MSL logs a review decision; it's persisted transactionally to
   Lakebase. Human-in-the-loop, always.

---

# The integrated journey (one governed flow)

```
Raw synthetic CSVs (UC Volume)
  → Lakeflow (Auto Loader)  → BRONZE (9 streaming tables)
  → SILVER  clean + ai_query() extracts structure from free-text MSL notes  ← Gen AI
  → GOLD    HCP 360 · priority · next-best-engagement · SLA · territory (metric views)
        → Genie      (natural-language Q&A)
        → Lakebase   (operational MSL action queue + review write-back)
        → App        (Medical Engagement Copilot)
Unity Catalog governs every object end-to-end (tags, PII class, lineage, scoped grants).
```

Lakeflow · Unity Catalog · Lakebase · Gen AI · Genie · Databricks App — **integrated, not
six disconnected demos.**

---

# Proof it ran (evidence in the repo, as text)

- **Lakeflow:** serverless pipeline `moa_medallion_febar` COMPLETED in 215s; 3,081 synthetic
  rows → bronze → silver → 13 gold tables.
- **Gen AI:** 500 free-text MSL notes → 500 structured rows; real before/after samples
  committed; live grounded briefing for the top KOL.
- **Lakebase:** 300-row action queue synced to Postgres; write-back table receiving MSL
  decisions; least-privilege SP grants.
- **Genie:** live NL question → correct SQL → answer ("SO-03 lowest reach at 26.3%").
- **App:** deployed, `ComputeState.ACTIVE`, deployment SUCCEEDED.
- **Governance:** UC tag policies enforced; `npi` classified PII.

*(See `evidence/01`–`09`.)*

---

# Decisions & trade-offs

- **SQL Lakeflow, serverless** — set-based transforms are most legible in SQL; `ai_query`
  is native. Materialized views give reproducible full refresh over non-deterministic AI.
- **Lakebase for OLTP serving** — Delta scans ≠ interactive cockpit; Lakebase adds
  millisecond lookups + transactional write-back while UC keeps one governance plane.
  `SNAPSHOT` sync fits daily MSL planning; CONTINUOUS is a one-line change.
- **Metric views** — one governed definition of "reach"/"engagement" shared by Genie and
  the app, so every surface agrees.
- **Human-in-the-loop, non-promotional** — every AI output is a reviewable recommendation,
  grounded only in the KOL's own governed signals; approved content only.

---

# AI as a force multiplier

Built end-to-end with Claude (Isaac) driving Databricks MCP tools + CLI: synthetic data,
pipeline authoring/run, Lakebase reverse-ETL + write-back, Genie, and app deployment —
including live debugging (metric-view YAML, `psycopg`→`pg8000` under Spark serverless, SDK
pinning).

**Next steps:** CONTINUOUS Lakebase sync for real-time queues · AI/BI dashboard on the same
metric views · MLflow-evaluated briefing quality · expand beyond oncology to full portfolio.

*All data synthetic. Medical Affairs (non-promotional). Recommendations require MSL review.*
