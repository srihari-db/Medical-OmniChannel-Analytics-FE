# Evidence 09 — Databricks App deployment (running)

The **Medical Engagement Copilot** (Streamlit) is deployed and running as a Databricks App,
surfacing the whole journey to the business.

## App details
```json
{
  "name": "moa-medical-copilot",
  "url": "https://moa-medical-copilot-984752964297111.11.azure.databricksapps.com",
  "status": "ComputeState.ACTIVE",
  "service_principal_client_id": "6b2f5b3e-b5e5-4573-9199-7164bff0b8f2",
  "service_principal_name": "app-7hspbl moa-medical-copilot"
}
```

## Deployment result
```json
{
  "deployment_id": "01f1b9f4bbe41641a2afaf4baedf1f91",
  "mode": "SNAPSHOT",
  "status": {"state": "SUCCEEDED", "message": "App started successfully"}
}
```

## Attached resources
```json
"resources": [
  {"name": "sql_warehouse", "sql_warehouse": {"id": "148ccb90800933a1", "permission": "CAN_USE"}},
  {"name": "lakebase", "database": {"instance_name": "moa-medical-copilot",
      "database_name": "databricks_postgres", "permission": "CAN_CONNECT_AND_CREATE"}}
]
```

## What the app does (all backends verified independently — see other evidence files)
- **MSL Action Queue tab** — low-latency read from Lakebase `public.msl_action_queue`.
- **HCP Pre-Engagement tab** — HCP 360 from governed Gold tables (SQL warehouse), a live
  `ai_query` briefing, a governed approved-content recommendation, and a **write-back form**
  that inserts the MSL's review decision into Lakebase `public.msl_review_actions`.

Source: `app/app.py`, `app/backend.py`, `app/app.yaml`, `app/requirements.txt`.
