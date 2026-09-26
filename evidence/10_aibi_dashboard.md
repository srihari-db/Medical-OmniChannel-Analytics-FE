# Evidence 10 — AI/BI dashboard (published)

AI/BI dashboard **"Medical Omnichannel Intelligence — Daiichi Sankyo"** built on the new
`_sa701.moa` gold tables and published. Every dataset query was validated via `execute_sql`
before deployment.

## Deployment result
```json
{
  "success": true,
  "status": "created",
  "dashboard_id": "01f1b9f6cf2119cdb68bbd5df75d577e",
  "path": "/Workspace/Users/srihari.a@databricks.com/Medical Omnichannel Intelligence — Daiichi Sankyo.lvdash.json",
  "url": "https://adb-984752964297111.11.azuredatabricks.net/sql/dashboardsv3/01f1b9f6cf2119cdb68bbd5df75d577e",
  "published": true
}
```
Definition committed at `dashboard/medical_omnichannel_intelligence.lvdash.json` (6 datasets, 16 widgets).

## Validated dataset results (tested before publishing)

**Headline KPIs (1 row):** total_hcps=300, priority_high=10, reach_90d_pct=0.437,
under_engaged=44, overdue_inquiries=140, avg_response_days=4.4

**90-day reach by territory (bar):**
| territory | reach_rate | under_engaged_priority |
|---|---:|---:|
| SO-03 | 26.3 | 5 |
| SO-01 | 26.9 | 8 |
| WE-02 | 44.2 | 4 |
| … | … | … |
| SO-02 | 57.9 | 4 |

**Scientific topic interest (bar):** Biomarker & Patient Selection 108 mentions / 93 HCPs;
Comparative Evidence 70; Long-term Efficacy & Outcomes 69; Safety / ILD Management 63;
Sequencing & Combinations 59; Real-World Evidence 54; …

**Medical inquiry SLA by product (bar):** Enhertu 109 inquiries / 32 overdue / 41.6% SLA-met;
Vanflyta 106 / 40 / 36.4%; HER3-DXd 104 / 38 / 46.2%; Datroway 81 / 30 / 43.1%

**Priority tier distribution (pie):** Medium 159, Low 131, High 10

**MSL next-best-engagement queue (table):** top 25 by priority score (Dr. Priya Kim 81.6, …).

## Widgets
6 KPI counters (total HCPs, 90-day reach, under-engaged priority KOLs, high-priority KOLs,
overdue inquiries, avg response days) · reach-by-territory bar · priority-tier pie · topic
interest bar · overdue-by-product bar · next-best-engagement table. The dashboard reuses the
same governed gold tables and metric-view logic as Genie and the app, so every surface agrees.
