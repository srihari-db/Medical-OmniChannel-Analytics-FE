-- =============================================================================
-- BRONZE — raw ingestion from the UC Volume via Auto Loader (read_files STREAM)
-- Source : /Volumes/_sa701/moa/raw/<dataset>/   (one folder per dataset)
-- Target : _sa701.moa.bronze_*   (pipeline default catalog/schema)
-- All data is SYNTHETIC (Daiichi Sankyo oncology Medical Affairs demo).
-- =============================================================================

CREATE OR REFRESH STREAMING TABLE bronze_hcp_master
  COMMENT 'Bronze: raw oncology HCP / KOL master records'
AS SELECT *, current_timestamp() AS _ingested_at, _metadata.file_path AS _source_file
FROM STREAM read_files(
  '/Volumes/_sa701/moa/raw/hcp_master/',
  format => 'csv', header => true,
  schemaHints => 'hcp_id STRING, publication_count INT, trial_participation INT, influence_score INT');

CREATE OR REFRESH STREAMING TABLE bronze_msl_interactions
  COMMENT 'Bronze: raw MSL field interactions incl. free-text raw_notes (GenAI input)'
AS SELECT *, current_timestamp() AS _ingested_at, _metadata.file_path AS _source_file
FROM STREAM read_files(
  '/Volumes/_sa701/moa/raw/msl_interactions/',
  format => 'csv', header => true, multiLine => true, escape => '"',
  schemaHints => 'interaction_id STRING, hcp_id STRING, interaction_date DATE, duration_minutes INT');

CREATE OR REFRESH STREAMING TABLE bronze_medical_inquiries
  COMMENT 'Bronze: raw medical information requests + SLA fields'
AS SELECT *, current_timestamp() AS _ingested_at, _metadata.file_path AS _source_file
FROM STREAM read_files(
  '/Volumes/_sa701/moa/raw/medical_inquiries/',
  format => 'csv', header => true,
  schemaHints => 'inquiry_id STRING, hcp_id STRING, inquiry_date DATE, response_time_days INT, sla_met BOOLEAN, sla_target_days INT');

CREATE OR REFRESH STREAMING TABLE bronze_congress_events
  COMMENT 'Bronze: raw congress / session attendance'
AS SELECT *, current_timestamp() AS _ingested_at, _metadata.file_path AS _source_file
FROM STREAM read_files(
  '/Volumes/_sa701/moa/raw/congress_events/',
  format => 'csv', header => true,
  schemaHints => 'event_attendance_id STRING, hcp_id STRING, event_date DATE, visited_medical_booth BOOLEAN');

CREATE OR REFRESH STREAMING TABLE bronze_digital_engagement
  COMMENT 'Bronze: raw digital / email / webinar engagement'
AS SELECT *, current_timestamp() AS _ingested_at, _metadata.file_path AS _source_file
FROM STREAM read_files(
  '/Volumes/_sa701/moa/raw/digital_engagement/',
  format => 'csv', header => true,
  schemaHints => 'engagement_id STRING, hcp_id STRING, activity_date DATE, emails_sent INT, emails_opened INT, webpage_clicks INT, attended_webinar BOOLEAN, content_minutes_viewed INT');

CREATE OR REFRESH STREAMING TABLE bronze_publications_trials
  COMMENT 'Bronze: raw publications & clinical trial participation'
AS SELECT *, current_timestamp() AS _ingested_at, _metadata.file_path AS _source_file
FROM STREAM read_files(
  '/Volumes/_sa701/moa/raw/publications_trials/',
  format => 'csv', header => true,
  schemaHints => 'record_id STRING, hcp_id STRING, year INT, citation_count INT');

CREATE OR REFRESH STREAMING TABLE bronze_patient_claims
  COMMENT 'Bronze: de-identified synthetic territory epidemiology summary'
AS SELECT *, current_timestamp() AS _ingested_at, _metadata.file_path AS _source_file
FROM STREAM read_files(
  '/Volumes/_sa701/moa/raw/patient_claims_summary/',
  format => 'csv', header => true,
  schemaHints => 'claim_summary_id STRING, diagnosed_patient_count INT, treated_patient_count INT, treatment_penetration_rate DOUBLE');

CREATE OR REFRESH STREAMING TABLE bronze_approved_content
  COMMENT 'Bronze: medically-approved content catalog'
AS SELECT *, current_timestamp() AS _ingested_at, _metadata.file_path AS _source_file
FROM STREAM read_files(
  '/Volumes/_sa701/moa/raw/approved_content/',
  format => 'csv', header => true,
  schemaHints => 'content_id STRING');

CREATE OR REFRESH STREAMING TABLE bronze_content_shared
  COMMENT 'Bronze: log of approved content shared with HCPs'
AS SELECT *, current_timestamp() AS _ingested_at, _metadata.file_path AS _source_file
FROM STREAM read_files(
  '/Volumes/_sa701/moa/raw/content_shared/',
  format => 'csv', header => true,
  schemaHints => 'share_id STRING, hcp_id STRING, content_id STRING, shared_date DATE');
