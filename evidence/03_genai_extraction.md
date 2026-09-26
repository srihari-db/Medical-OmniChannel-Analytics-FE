# Evidence 03 — Gen AI extraction (unstructured MSL notes → structured signals)

`silver_msl_extracted` is produced inside the Lakeflow pipeline by calling
`ai_query('databricks-meta-llama-3-3-70b-instruct', …)` on each free-text MSL note,
returning JSON that is parsed into 10+ typed columns and bucketed into a
`topic_category`. This is the "make it intelligent" stage, executed on real data.

## Before → after (3 real rows)

**Row 1**
- **raw_notes:** *"Met with the HCP via congress to discuss combination strategies with immunotherapy for HER3-DXd (patritumab deruxtecan (pipeline)) in EGFR-mutant NSCLC (investigational). Overall t…"*
- **extracted:** scientific_topic=`Immunotherapy combination strategies`, topic_category=`Sequencing & Combinations`, sentiment=`Positive`, interest_level=`Medium`, follow_up_requested=`true`, competitor_mentioned=`Trodelvy`, evidence_type_requested=`Subgroup analysis`

**Row 2**
- **raw_notes:** *"Met with the HCP via virtual to discuss long-term duration of response and survival outcomes for HER3-DXd … in EGFR-mutant NSCLC (investigational)."*
- **extracted:** scientific_topic=`Biomarker evidence and safety management`, topic_category=`Safety / ILD Management`, sentiment=`Neutral`, interest_level=`High`, follow_up_requested=`true`, competitor_mentioned=`Tukysa`, evidence_type_requested=`Biomarker evidence`

**Row 3**
- **raw_notes:** *"Met with the HCP via email to discuss real-world outcomes and treatment patterns post-T-DXd for HER3-DXd … in EGFR-mutant NSCLC (investigational)."*
- **extracted:** scientific_topic=`Real-world outcomes and treatment patterns`, topic_category=`Real-World Evidence`, sentiment=`Positive`, interest_level=`High`, follow_up_requested=`false`, competitor_mentioned=`Phesgo`, evidence_type_requested=`Real-world evidence`

## Extraction distribution (top combinations across all 500 notes)

| topic_category | sentiment | interest | rows |
|---|---|---|---:|
| Biomarker & Patient Selection | Neutral | High | 21 |
| Comparative Evidence | Neutral | High | 19 |
| Biomarker & Patient Selection | Positive | Medium | 18 |
| Sequencing & Combinations | Neutral | Medium | 16 |
| Long-term Efficacy & Outcomes | Neutral | Medium | 15 |
| Biomarker & Patient Selection | Positive | High | 14 |
| Real-World Evidence | Positive | High | 11 |
| Safety / ILD Management | Neutral | High | 11 |
| CNS / Brain Metastases | Positive | Medium | 9 |

The model correctly maps varied free-text into the governed oncology topic taxonomy
(ILD safety, HER2/TROP2 biomarkers, CNS, sequencing, RWE, comparative evidence) and
extracts sentiment, interest, competitor mentions and evidence needs — the signals that
drive the downstream priority and next-best-engagement scoring.
