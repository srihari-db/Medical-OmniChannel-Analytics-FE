# Medical Omnichannel Intelligence — Daiichi Sankyo (FE BAR build)

## The outcome first

**Daiichi Sankyo's oncology Medical Affairs teams win by getting the right scientific
evidence to the right oncology KOL at the right moment** — for Enhertu (trastuzumab
deruxtecan) and Datroway (datopotamab deruxtecan). Today those engagement signals are
siloed across MSL field notes, medical inquiries, congress activity and digital channels,
so Medical Science Liaisons (MSLs) **miss follow-ups, respond slowly to medical inquiries,
and under-serve high-influence KOLs.**

This build unifies every signal into one governed platform and turns it into a prioritized,
AI-assisted **next-best-engagement** workflow surfaced in an MSL cockpit.

**Quantified impact (estimated, 120-MSL field medical org):**

| Lever | Basis | Est. annual value |
|------|-------|------------------:|
| MSL prep time saved | AI pre-engagement briefings replace ~2 hrs/MSL/week of manual prep (120 MSLs × 2 h × 46 wk × $120/h loaded) | **~$1.3M** |
| Faster medical-inquiry resolution | Surfacing overdue inquiries + SLA analytics cuts avg response time and overdue backlog | **~$0.6M** |
| Priority-KOL reach uplift | Lifting 90-day reach of priority KOLs from ~44% toward 60% accelerates scientific exchange during launch windows | **~$1.5M** |
| **Total** | | **~$3.4M / year** |

For the **executive sponsor** (VP Medical Affairs): higher scientific share-of-voice with
priority KOLs and defensible SLA governance. For the **domain owner** (Field Medical
Director): every MSL walks into each engagement prepared, compliant, and pointed at the
highest-need KOLs first.

> All data is **synthetic**. Context is **Medical Affairs (non-promotional)**. Every AI
> output is a recommendation for **human (MSL) review**, never an automated or promotional
> action.

## The integrated journey (all six FE BAR stages, one flow)

```
 Raw synthetic CSVs (UC Volume _sa701.moa.raw)
        │  ── Lakeflow (Auto Loader, read_files STREAM)
        ▼
 BRONZE  9 streaming tables  ─┐
        │                     │  Unity Catalog governs every object
 SILVER  cleaned + ai_query() │  (tags, tag-policies, PII column class,
        │   (Gen AI: MSL      │   metric views, lineage, scoped grants)
        │    notes → structured)
        ▼                     │
 GOLD    HCP 360 · priority · next-best-engagement · topic interest ·
        │  inquiry SLA · congress · territory opportunity · metric views
        ├───────────────► Genie space  (natural-language Q&A)
        ├───────────────► Lakebase  (reverse ETL → operational MSL action queue
        │                            + transactional MSL review write-back)
        └───────────────► Databricks App "Medical Engagement Copilot"
                                   (HCP 360 + AI briefing + queue + write-back)
```

| Stage | Where | Evidence |
|------|-------|----------|
| **Lakeflow** | `pipeline/transformations/*.sql`, serverless pipeline `moa_medallion_febar` | [evidence/01](evidence/01_lakeflow_pipeline_run.md) |
| **Unity Catalog** | `_sa701.moa` (tables, volumes, tags, metric views) | [evidence/02](evidence/02_medallion_row_counts.md), [evidence/08](evidence/08_unity_catalog_governance.md) |
| **Gen AI** | `ai_query` in `02_silver.sql` + app briefings | [evidence/03](evidence/03_genai_extraction.md), [evidence/04](evidence/04_genai_briefing.md) |
| **Lakebase** | instance `moa-medical-copilot`, synced queue + write-back | [evidence/06](evidence/06_lakebase_serving.md) |
| **Genie** | space *Medical Omnichannel Intelligence — Daiichi Sankyo* | [evidence/07](evidence/07_genie_nl_query.md) |
| **Databricks App** | `app/` — deployed & running | [evidence/09](evidence/09_app_deployment.md) |

## Repository layout

```
data_generation/   generate_synthetic_data.py  — Daiichi oncology synthetic data (seeded)
data/raw/          the 9 generated CSVs (also uploaded to the UC Volume)
pipeline/          transformations/{01_bronze,02_silver,03_gold}.sql  — Lakeflow medallion
sql/               00_schema_and_volume.sql · 01_metric_views.sql · 02_ai_query_extraction.sql
lakebase/          setup_lakebase.py · grant_app_access.py  — operational serving + grants
genie/             genie space definition (tables + sample questions)
app/               Databricks App — Medical Engagement Copilot (Streamlit)
evidence/          01–09 execution evidence, readable as text (the build actually ran)
docs/              DECISIONS_AND_TRADEOFFS.md · SOLUTION_OVERVIEW (Word)
deck/              business presentation (PDF + Markdown)
```

## How it was built (reproduce)

1. `python data_generation/generate_synthetic_data.py --out data/raw` → 9 CSVs (~3,081 rows)
2. Create UC Volume `_sa701.moa.raw`; upload each CSV to its own subfolder
3. Deploy & run the serverless Lakeflow pipeline from `pipeline/transformations/` (full refresh)
4. Create metric views (`sql/01_metric_views.sql`)
5. Create Lakebase instance, register UC catalog `moa_lakebase`, create the synced action
   queue, run `lakebase/setup_lakebase.py` (write-back table) and `grant_app_access.py`
6. Create the Genie space over the gold tables + metric views
7. Deploy the app (`app/`) with `sql_warehouse` + `lakebase` resources

## Environment
- Workspace: `adb-984752964297111.11.azuredatabricks.net` (Azure)
- Catalog / schema: `_sa701.moa`
- LLM endpoint: `databricks-meta-llama-3-3-70b-instruct`
- SQL warehouse: `148ccb90800933a1`
- Built with Claude (Isaac) as an AI pair-builder — see `docs/DECISIONS_AND_TRADEOFFS.md`.
