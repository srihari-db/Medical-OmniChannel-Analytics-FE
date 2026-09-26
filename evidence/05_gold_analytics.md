# Evidence 05 — Gold analytics & governed metric views

## Governed metric view `metric_hcp_engagement` — by territory
`SELECT Territory, MEASURE(`Total HCPs`), MEASURE(`HCPs Engaged 90d`), MEASURE(`HCP Reach Pct`) … GROUP BY Territory`

| Territory | Total HCPs | Engaged 90d | Reach % | Under-Engaged Priority | Avg Eng | Avg Need |
|---|---:|---:|---:|---:|---:|---:|
| WE-02 | 52 | 23 | 44.2 | 4 | 25.9 | 18.4 |
| SO-03 | 38 | 10 | 26.3 | 5 | 19.0 | 14.1 |
| WE-01 | 34 | 16 | 47.1 | 8 | 25.6 | 15.7 |
| WE-03 | 29 | 13 | 44.8 | 4 | 23.2 | 18.4 |
| NE-02 | 27 | 12 | 44.4 | 1 | 20.3 | 19.8 |
| SO-01 | 26 | 7 | 26.9 | 8 | 14.6 | 15.4 |
| NE-03 | 24 | 13 | 54.2 | 2 | 25.2 | 18.0 |
| MW-02 | 21 | 12 | 57.1 | 2 | 26.5 | 24.9 |
| MW-01 | 20 | 9 | 45.0 | 3 | 25.8 | 18.6 |
| SO-02 | 19 | 11 | 57.9 | 4 | 29.3 | 16.2 |
| NE-01 | 10 | 5 | 50.0 | 3 | 25.8 | 11.9 |

The same governed metric view is reused by the Genie space and (conceptually) the AI/BI
dashboard — one definition of "HCP reach", "engagement score", etc.

## `gold_next_best_engagement` — top MSL priorities

| HCP | Territory | Tier | Score | Trigger | Topic | Recommended by |
|---|---|---|---:|---|---|---|
| Dr. Priya Kim | NE-03 | High | 81.6 | Open medical inquiry overdue | Real-World Evidence | 2026-10-10 |
| Dr. Aisha Khan | SO-03 | High | 71.9 | Open medical inquiry overdue | Sequencing & Combinations | 2026-10-10 |
| Dr. William Khan | SO-03 | High | 71.0 | Open medical inquiry overdue | Long-term Efficacy & Outcomes | 2026-10-10 |
| Dr. Nina Smith | WE-02 | High | 68.6 | Open medical inquiry overdue | Biomarker & Patient Selection | 2026-10-10 |
| Dr. William Davis | SO-01 | High | 67.2 | Open medical inquiry overdue | General Scientific Exchange | 2026-10-10 |
| Dr. Laura Kim | WE-01 | High | 67.1 | Open medical inquiry overdue | Biomarker & Patient Selection | 2026-10-10 |

Each recommendation carries a concrete `suggested_engagement` string (e.g. *"Address
Safety management guidance with approved evidence on Real-World Evidence"*), a preferred
channel, and a recommended date — a specific, reviewable next action, not a generic score.
