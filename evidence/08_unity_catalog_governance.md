# Evidence 08 — Unity Catalog governance

All assets live under one governed namespace `_sa701.moa`, with UC tags (governed by
workspace **tag policies** — only policy-approved values are accepted), column-level
sensitivity classification, and scoped grants to the app service principal.

## Tags applied (queried from `information_schema`)
```
schema  moa   domain              = clinical
schema  moa   data_classification = internal
column  gold_hcp_360.npi          sensitivity        = pii
column  gold_hcp_360.npi          data_classification = pii
table   gold_next_best_engagement layer              = gold
table   gold_next_best_engagement serving            = lakebase_operational
table   gold_next_best_engagement review_required    = msl_human_in_the_loop
table   gold_hcp_priority         layer              = gold
table   gold_hcp_priority         serving            = lakebase_operational
```

Note: the workspace enforces UC **tag policies** — e.g. `domain` only accepts
`[finance, sales, marketing, r&d, operations, clinical, …]` and `data_classification`
only `[public, internal, confidential, pii, restricted]`. Values were chosen to comply,
demonstrating governance is actively enforced, not cosmetic.

## Least-privilege grants to the Databricks App service principal
```
GRANT USE CATALOG ON CATALOG _sa701            TO `6b2f5b3e-b5e5-4573-9199-7164bff0b8f2`
GRANT USE SCHEMA  ON SCHEMA  _sa701.moa         TO `6b2f5b3e-b5e5-4573-9199-7164bff0b8f2`
GRANT SELECT      ON SCHEMA  _sa701.moa         TO `6b2f5b3e-b5e5-4573-9199-7164bff0b8f2`
```
Plus Lakebase Postgres grants (evidence 06): `SELECT` on the synced queue, `SELECT, INSERT`
on the write-back table — the app reads governed data and Lakebase with exactly the
privileges it needs.

## Governed objects in `_sa701.moa`
- 9 bronze streaming tables, 9 silver materialized views, 13 gold materialized views
- 1 serving table (`serving_msl_action_queue`, PK `hcp_id`)
- 2 metric views (`metric_hcp_engagement`, `metric_medical_inquiries`)
- 2 volumes (`raw`, `source_documents`)
- Lineage from Volume → bronze → silver → gold → metric views → Genie / Lakebase / app is
  captured automatically by UC.
