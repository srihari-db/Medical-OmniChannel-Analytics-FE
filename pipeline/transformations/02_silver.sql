-- =============================================================================
-- SILVER — cleaned / validated entities + the GenAI extraction step
-- Reads bronze_* (same pipeline), writes _sa701.moa.silver_*
-- =============================================================================

-- HCP master (dedup + trim) -------------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW silver_hcp
  COMMENT 'Silver: deduplicated, cleaned oncology HCP master'
AS
SELECT hcp_id, trim(hcp_name) AS hcp_name, specialty, institution, city, state, territory,
       practice_setting, hcp_tier, primary_therapeutic_area,
       CAST(publication_count AS INT) AS publication_count,
       CAST(trial_participation AS INT) AS trial_participation,
       CAST(influence_score AS INT) AS influence_score, npi
FROM (SELECT *, row_number() OVER (PARTITION BY hcp_id ORDER BY _ingested_at DESC) AS rn
      FROM bronze_hcp_master) WHERE rn = 1 AND hcp_id IS NOT NULL;

-- Medical inquiries (typed + overdue flag) ----------------------------------
CREATE OR REFRESH MATERIALIZED VIEW silver_medical_inquiries
  COMMENT 'Silver: medical information requests with SLA + overdue derivation'
AS
SELECT inquiry_id, hcp_id, inquiry_date, inquiry_topic, evidence_type_requested, indication,
       product, response_status, response_time_days, sla_target_days, sla_met,
       (response_status <> 'Closed' AND datediff(current_date(), inquiry_date) > sla_target_days) AS overdue
FROM bronze_medical_inquiries WHERE inquiry_id IS NOT NULL;

-- Congress attendance -------------------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW silver_congress
  COMMENT 'Silver: cleaned congress / session attendance'
AS
SELECT event_attendance_id, hcp_id, event_name, event_date, session_topic, therapeutic_area,
       attendance_status, visited_medical_booth
FROM bronze_congress_events WHERE event_attendance_id IS NOT NULL;

-- Digital engagement --------------------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW silver_digital
  COMMENT 'Silver: cleaned digital / email / webinar engagement'
AS
SELECT engagement_id, hcp_id, activity_date, emails_sent, emails_opened, content_title,
       content_type, webpage_clicks, attended_webinar, content_minutes_viewed
FROM bronze_digital_engagement WHERE engagement_id IS NOT NULL;

-- Publications & trials -----------------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW silver_publications
  COMMENT 'Silver: cleaned publications & clinical-trial participation'
AS
SELECT record_id, hcp_id, record_type, title, journal_or_registry, year, therapeutic_area,
       trial_id, citation_count
FROM bronze_publications_trials WHERE record_id IS NOT NULL;

-- Patient claims summary ----------------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW silver_claims
  COMMENT 'Silver: synthetic de-identified territory epidemiology'
AS
SELECT claim_summary_id, city, state, territory, diagnosis, primary_therapy,
       diagnosed_patient_count, treated_patient_count, treatment_penetration_rate
FROM bronze_patient_claims WHERE claim_summary_id IS NOT NULL;

-- Approved content catalog --------------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW silver_approved_content
  COMMENT 'Silver: medically-approved content catalog'
AS
SELECT content_id, content_title, content_type, topic_category, indication, product,
       approval_date, approval_status, med_review_id
FROM bronze_approved_content WHERE content_id IS NOT NULL;

-- Content shared log --------------------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW silver_content_shared
  COMMENT 'Silver: log of approved content shared with HCPs'
AS
SELECT share_id, hcp_id, content_id, content_title, content_type, topic_category,
       shared_date, shared_by_msl, share_channel
FROM bronze_content_shared WHERE share_id IS NOT NULL;

-- ===========================================================================
-- SILVER GENAI — structure extracted from free-text MSL notes via ai_query()
-- Model: databricks-meta-llama-3-3-70b-instruct. One LLM call per interaction.
-- ===========================================================================
CREATE OR REFRESH MATERIALIZED VIEW silver_msl_extracted
  COMMENT 'Silver (GenAI): 10+ structured fields extracted from MSL raw_notes with ai_query'
AS
WITH raw AS (
  SELECT interaction_id, hcp_id, msl_name, interaction_date, channel, duration_minutes, raw_notes,
    regexp_replace(
      ai_query(
        'databricks-meta-llama-3-3-70b-instruct',
        concat(
          'You are a Medical Affairs analyst. Extract structured fields from this MSL interaction note as JSON with EXACTLY these keys: ',
          'therapeutic_area, scientific_topic, information_need, product_or_indication, sentiment (one of Positive/Neutral/Negative), ',
          'interest_level (one of High/Medium/Low), follow_up_requested (true or false), competitor_mentioned (competitor name or None), ',
          'preferred_channel (one of In-person/Virtual/Phone/Email/Congress/None), evidence_type_requested. ',
          'Return ONLY valid minified JSON, no markdown, no prose. Note: ', raw_notes)
      ), '```(json)?', '') AS extracted_raw
  FROM bronze_msl_interactions
),
parsed AS (
  SELECT *, from_json(trim(extracted_raw),
    'therapeutic_area STRING, scientific_topic STRING, information_need STRING, product_or_indication STRING, sentiment STRING, interest_level STRING, follow_up_requested BOOLEAN, competitor_mentioned STRING, preferred_channel STRING, evidence_type_requested STRING') AS j
  FROM raw
),
fixed AS (
  SELECT interaction_id, hcp_id, msl_name, interaction_date, channel, duration_minutes,
    coalesce(j.therapeutic_area, 'Oncology') AS therapeutic_area,
    coalesce(j.scientific_topic, 'General scientific exchange') AS scientific_topic,
    coalesce(j.information_need, 'Scientific information request') AS information_need,
    coalesce(j.product_or_indication, 'Portfolio') AS product_or_indication,
    coalesce(j.sentiment, 'Neutral') AS sentiment,
    coalesce(j.interest_level, 'Medium') AS interest_level,
    coalesce(j.follow_up_requested, false) AS follow_up_requested,
    coalesce(j.competitor_mentioned, 'None') AS competitor_mentioned,
    coalesce(nullif(j.preferred_channel, 'None'), channel) AS preferred_channel,
    coalesce(j.evidence_type_requested, 'Efficacy') AS evidence_type_requested,
    CASE WHEN j.follow_up_requested THEN date_add(interaction_date, 14) ELSE NULL END AS recommended_follow_up_date,
    raw_notes
  FROM parsed
)
SELECT *,
  CASE
    WHEN lower(scientific_topic) RLIKE 'ild|pneumonitis|interstitial|lung|safety|adverse|toxicity' THEN 'Safety / ILD Management'
    WHEN lower(scientific_topic) RLIKE 'real-world|rwe|real world' THEN 'Real-World Evidence'
    WHEN lower(scientific_topic) RLIKE 'long-term|duration of response|outcome|survival' THEN 'Long-term Efficacy & Outcomes'
    WHEN lower(scientific_topic) RLIKE 'biomarker|trop2|her2|testing|diagnostic|selection|amplif|ihc' THEN 'Biomarker & Patient Selection'
    WHEN lower(scientific_topic) RLIKE 'cns|brain|metasta' THEN 'CNS / Brain Metastases'
    WHEN lower(scientific_topic) RLIKE 'dosing|dose|administration|nausea|management' THEN 'Dosing & Administration'
    WHEN lower(scientific_topic) RLIKE 'sequenc|resistance|combination|immunotherap' THEN 'Sequencing & Combinations'
    WHEN lower(scientific_topic) RLIKE 'comparative|head-to-head|versus|compar' THEN 'Comparative Evidence'
    WHEN lower(scientific_topic) RLIKE 'efficacy' THEN 'Long-term Efficacy & Outcomes'
    ELSE 'General Scientific Exchange'
  END AS topic_category
FROM fixed;
