# Evidence 07 — Genie Agent (natural-language querying)

Genie space **"Medical Omnichannel Intelligence — Daiichi Sankyo"**
(`space_id 01f1b9f40b3d1499a1dde849fe4ecaf0`, 9 tables incl. gold + governed metric views).

## Live question asked via the Genie Conversation API

**Question:** *"Which 5 territories have the lowest 90-day HCP reach rate, and how many
under-engaged priority HCPs does each have?"*

**Genie-generated SQL:**
```sql
WITH ranked AS (
  SELECT `territory`, `reach_rate`, `under_engaged_priority_hcps`,
         RANK() OVER (ORDER BY `reach_rate` ASC) AS `reach_rank`
  FROM `_sa701`.`moa`.`gold_territory_opportunity`
  WHERE `territory` IS NOT NULL AND `reach_rate` IS NOT NULL
    AND `under_engaged_priority_hcps` IS NOT NULL)
SELECT `territory`, `reach_rate`, `under_engaged_priority_hcps`
FROM ranked WHERE `reach_rank` <= 5
ORDER BY `reach_rate` ASC, `territory` ASC
```

**Result (row_count = 5):**
| territory | reach_rate | under_engaged_priority_hcps |
|---|---:|---:|
| SO-03 | 26.3 | 5 |
| SO-01 | 26.9 | 8 |
| WE-02 | 44.2 | 4 |
| NE-02 | 44.4 | 1 |
| WE-03 | 44.8 | 4 |

**Genie natural-language answer:**
> The 5 territories with the lowest 90-day HCP reach rate are: SO-03 — 26.3% reach and 5
> under-engaged priority HCPs; SO-01 — 26.9% and 8; WE-02 — 44.2% and 4; NE-02 — 44.4% and 1;
> WE-03 — 44.8% and 4. Among these five, SO-01 has the most under-engaged priority HCPs (8),
> while SO-03 has the lowest reach rate (26.3%).

Genie correctly interpreted the business question, wrote valid SQL against the governed
gold table, executed it, and summarized the answer in natural language — the "queryable in
natural language" stage, working end-to-end.
