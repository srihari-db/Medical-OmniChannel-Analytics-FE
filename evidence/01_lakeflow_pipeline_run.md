# Evidence 01 — Lakeflow pipeline execution

Serverless **Lakeflow Spark Declarative Pipeline** `moa_medallion_febar` ingesting the
raw UC Volume files through Bronze → Silver (incl. the Gen AI extraction) → Gold.

## Pipeline run result (create + full refresh)

```json
{
  "pipeline_id": "8361155d-f4bb-4a33-b1c1-3219f04fef33",
  "pipeline_name": "moa_medallion_febar",
  "update_id": "73d95dfa-777e-4e3e-a6fd-36ab9e86f8b0",
  "state": "COMPLETED",
  "success": true,
  "created": true,
  "catalog": "_sa701",
  "schema": "moa",
  "duration_seconds": 214.66,
  "message": "Pipeline created and completed successfully in 214.66s. Tables written to _sa701.moa"
}
```

- **Compute:** serverless
- **Source:** `/Volumes/_sa701/moa/raw/<dataset>/` (9 dataset folders, CSV, Auto Loader `read_files` STREAM)
- **Transformations:** `pipeline/transformations/01_bronze.sql`, `02_silver.sql`, `03_gold.sql`
- **Outcome:** 9 bronze streaming tables, 9 silver materialized views (incl. `silver_msl_extracted`
  produced by `ai_query`), 13 gold materialized views. All `COMPLETED`, 0 errors.

The run wrote every bronze/silver/gold object into `_sa701.moa` in a single DAG — the journey is
integrated (Lakeflow → Unity Catalog), not a set of hand-run scripts.
