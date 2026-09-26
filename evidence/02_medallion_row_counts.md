# Evidence 02 — Medallion table row counts

Query run against the SQL warehouse after the Lakeflow pipeline completed
(`SELECT COUNT(*)` per table in `_sa701.moa`).

| Table | Layer | Rows |
|-------|-------|-----:|
| `bronze_msl_interactions` | Bronze | 500 |
| `silver_msl_extracted` | Silver (Gen AI) | 500 |
| `gold_hcp_360` | Gold | 300 |
| `gold_hcp_priority` | Gold | 300 |
| `gold_next_best_engagement` | Gold | 300 |
| `gold_hcp_channel_engagement` | Gold | 300 |
| `gold_medical_topic_interest` | Gold | 446 |
| `gold_medical_information_requests` | Gold | 400 |
| `gold_congress_engagement` | Gold | 227 |
| `gold_territory_opportunity` | Gold | 11 |
| `gold_approved_content` | Gold | 70 |
| `gold_content_shared` | Gold | 320 |
| `gold_publications_trials` | Gold | 350 |

Raw inputs (in `/Volumes/_sa701/moa/raw/`): hcp_master 300, msl_interactions 500,
medical_inquiries 400, congress_events 420, digital_engagement 500,
publications_trials 350, patient_claims_summary 221, approved_content 70,
content_shared 320 — **3,081 synthetic rows total**.

Every MSL free-text note (500) produced exactly one structured silver row (500) — the
`ai_query` extraction had full coverage. 300 HCPs flow cleanly to the 360 / priority /
next-best-engagement gold tables.
