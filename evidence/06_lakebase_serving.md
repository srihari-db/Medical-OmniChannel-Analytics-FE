# Evidence 06 — Lakebase operational serving (reverse ETL + write-back)

Lakebase Provisioned instance **`moa-medical-copilot`** (PostgreSQL 16, CU_1,
`ep-aged-breeze-e18tpa3f.database.eastus2.azuredatabricks.net`), registered in Unity
Catalog as catalog **`moa_lakebase`** (database `databricks_postgres`).

## 1. Reverse ETL — Gold Delta → Lakebase synced table
`_sa701.moa.serving_msl_action_queue` (300 rows, PK `hcp_id`) is synced to
`moa_lakebase.public.msl_action_queue` via a `SNAPSHOT` synced table:

```json
{"data_synchronization_status": {"detailed_state": "SYNCED_TABLE_PROVISIONING_INITIAL_SNAPSHOT",
 "message": "Synced table creation successful, pipeline running.",
 "pipeline_id": "36ec87c5-1d01-4598-8baa-c115622529cb"},
 "name": "moa_lakebase.public.msl_action_queue",
 "spec": {"primary_key_columns": ["hcp_id"], "scheduling_policy": "SNAPSHOT",
          "source_table_full_name": "_sa701.moa.serving_msl_action_queue"}}
```

## 2. Reading the queue from Lakebase (setup job log, pg8000 on serverless)
```
[synced] public.msl_action_queue rows = 300
[synced] top-5 MSL priorities:
    ['HCP-00020', 'Dr. Priya Kim', 'High', Decimal('81.6'), 'Open medical inquiry overdue']
    ['HCP-00119', 'Dr. Aisha Khan', 'High', Decimal('71.9'), 'Open medical inquiry overdue']
    ['HCP-00112', 'Dr. William Khan', 'High', Decimal('71.0'), 'Open medical inquiry overdue']
    ['HCP-00200', 'Dr. Nina Smith', 'High', Decimal('68.6'), 'Open medical inquiry overdue']
    ['HCP-00038', 'Dr. William Davis', 'High', Decimal('67.2'), 'Open medical inquiry overdue']
```
The synced table is also queryable through UC from the SQL warehouse
(`SELECT … FROM moa_lakebase.public.msl_action_queue`) — verified, returns the same rows.

## 3. Operational write-back — MSL review decisions
`public.msl_review_actions` (BIGSERIAL PK, indexed on `hcp_id`) receives MSL decisions
from the app. Setup job log:
```
[write-back] seeded 2 demo review actions
[write-back] public.msl_review_actions rows = 2
[conn] connected as ['srihari.a@databricks.com', 'databricks_postgres']
DONE: Lakebase operational serving ready.
```

## 4. App service-principal grants (least privilege)
```
candidate SP roles: ['6b2f5b3e-b5e5-4573-9199-7164bff0b8f2']
granted read/write to 6b2f5b3e-b5e5-4573-9199-7164bff0b8f2
```
The app SP has `SELECT` on `msl_action_queue` and `SELECT, INSERT` on `msl_review_actions`
only — the operational read/write loop is closed with scoped permissions.

**Why Lakebase here:** the analytical Gold tables live in Delta (great for scans/joins),
but an MSL cockpit needs millisecond point lookups and transactional write-back of review
decisions. Lakebase serves the operational layer while UC keeps one governance plane.
