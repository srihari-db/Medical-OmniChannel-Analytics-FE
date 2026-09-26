-- =============================================================================
-- GOLD — business-ready analytics for MSL next-best-engagement & the app/Genie
-- Reads silver_* (same pipeline), writes _sa701.moa.gold_*
-- =============================================================================

-- Passthrough golds (consumable naming) -------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW gold_medical_information_requests
  COMMENT 'Gold: medical information requests with SLA + overdue'
AS SELECT inquiry_id, hcp_id, inquiry_date, inquiry_topic, evidence_type_requested, indication,
          product, response_status, response_time_days, sla_target_days, sla_met, overdue
   FROM silver_medical_inquiries;

CREATE OR REFRESH MATERIALIZED VIEW gold_publications_trials
  COMMENT 'Gold: publications & trials (consumable)'
AS SELECT * FROM silver_publications;

CREATE OR REFRESH MATERIALIZED VIEW gold_approved_content
  COMMENT 'Gold: approved content catalog (consumable)'
AS SELECT * FROM silver_approved_content;

CREATE OR REFRESH MATERIALIZED VIEW gold_content_shared
  COMMENT 'Gold: approved content shared with HCPs (consumable)'
AS SELECT * FROM silver_content_shared;

-- MSL interaction summary per HCP -------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW gold_msl_interaction_summary
  COMMENT 'Gold: per-HCP MSL interaction recency & cadence'
AS
SELECT hcp_id,
  COUNT(*) AS total_interactions,
  COUNT(CASE WHEN datediff(current_date(), interaction_date) <= 30  THEN 1 END) AS interactions_30d,
  COUNT(CASE WHEN datediff(current_date(), interaction_date) <= 90  THEN 1 END) AS interactions_90d,
  COUNT(CASE WHEN datediff(current_date(), interaction_date) <= 180 THEN 1 END) AS interactions_180d,
  ROUND(AVG(duration_minutes), 1) AS avg_duration_min,
  MAX(interaction_date) AS last_interaction_date,
  datediff(current_date(), MAX(interaction_date)) AS days_since_last_interaction,
  COUNT(CASE WHEN follow_up_requested THEN 1 END) AS follow_ups_requested,
  COUNT(DISTINCT topic_category) AS distinct_topics,
  MAX(sentiment) AS sample_sentiment
FROM silver_msl_extracted GROUP BY hcp_id;

-- Topic interest per HCP ----------------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW gold_medical_topic_interest
  COMMENT 'Gold: per-HCP scientific topic interest scoring'
AS
SELECT hcp_id, topic_category,
  COUNT(*) AS mentions,
  COUNT(CASE WHEN datediff(current_date(), interaction_date) <= 30 THEN 1 END) AS mentions_current_30d,
  COUNT(CASE WHEN datediff(current_date(), interaction_date) BETWEEN 31 AND 60 THEN 1 END) AS mentions_prior_30d,
  ROUND(AVG(CASE interest_level WHEN 'High' THEN 3 WHEN 'Medium' THEN 2 ELSE 1 END), 2) AS avg_interest_weight,
  MAX(interaction_date) AS last_mention_date,
  ROUND(COUNT(*) * 10
        + COUNT(CASE WHEN datediff(current_date(), interaction_date) <= 30 THEN 1 END) * 8
        + AVG(CASE interest_level WHEN 'High' THEN 3 WHEN 'Medium' THEN 2 ELSE 1 END) * 6, 1) AS topic_interest_score
FROM silver_msl_extracted GROUP BY hcp_id, topic_category;

-- Congress engagement per HCP -----------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW gold_congress_engagement
  COMMENT 'Gold: per-HCP congress participation'
AS
SELECT c.hcp_id, h.hcp_name, h.territory, h.specialty,
  COUNT(*) AS sessions_registered,
  COUNT(CASE WHEN c.attendance_status = 'Attended' THEN 1 END) AS sessions_attended,
  COUNT(CASE WHEN c.visited_medical_booth THEN 1 END) AS booth_visits,
  COUNT(DISTINCT c.event_name) AS distinct_events,
  array_distinct(collect_list(c.session_topic)) AS session_topics,
  MAX(c.event_date) AS last_congress_date
FROM silver_congress c LEFT JOIN silver_hcp h USING (hcp_id)
GROUP BY c.hcp_id, h.hcp_name, h.territory, h.specialty;

-- Omnichannel engagement per HCP --------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW gold_hcp_channel_engagement
  COMMENT 'Gold: per-HCP omnichannel engagement rollup'
AS
WITH d AS (
  SELECT hcp_id, SUM(emails_sent) AS emails_sent, SUM(emails_opened) AS emails_opened,
    SUM(webpage_clicks) AS webpage_clicks, COUNT(CASE WHEN attended_webinar THEN 1 END) AS webinars_attended,
    MAX(activity_date) AS last_digital_date
  FROM silver_digital GROUP BY hcp_id),
m AS (SELECT hcp_id, COUNT(*) AS msl_interactions, ROUND(AVG(duration_minutes),1) AS avg_msl_duration_min,
        MAX(interaction_date) AS last_msl_date FROM silver_msl_extracted GROUP BY hcp_id),
cg AS (SELECT hcp_id, COUNT(CASE WHEN attendance_status='Attended' THEN 1 END) AS congress_sessions_attended,
        MAX(event_date) AS last_congress_date FROM silver_congress GROUP BY hcp_id),
inq AS (SELECT hcp_id, COUNT(*) AS medical_inquiries, MAX(inquiry_date) AS last_inquiry_date
        FROM silver_medical_inquiries GROUP BY hcp_id)
SELECT h.hcp_id, h.hcp_name, h.territory, h.specialty,
  coalesce(m.msl_interactions,0) AS msl_interactions, m.avg_msl_duration_min,
  coalesce(d.emails_sent,0) AS emails_sent, coalesce(d.emails_opened,0) AS emails_opened,
  ROUND(coalesce(d.emails_opened,0)/NULLIF(d.emails_sent,0),3) AS email_open_rate,
  coalesce(d.webpage_clicks,0) AS webpage_clicks, coalesce(d.webinars_attended,0) AS webinars_attended,
  coalesce(cg.congress_sessions_attended,0) AS congress_sessions_attended,
  coalesce(inq.medical_inquiries,0) AS medical_inquiries,
  (CASE WHEN coalesce(m.msl_interactions,0)>0 THEN 1 ELSE 0 END
   + CASE WHEN coalesce(d.emails_sent,0)>0 THEN 1 ELSE 0 END
   + CASE WHEN coalesce(cg.congress_sessions_attended,0)>0 THEN 1 ELSE 0 END
   + CASE WHEN coalesce(inq.medical_inquiries,0)>0 THEN 1 ELSE 0 END) AS channels_used,
  m.last_msl_date, d.last_digital_date, cg.last_congress_date, inq.last_inquiry_date,
  greatest(coalesce(m.last_msl_date,DATE'2000-01-01'), coalesce(d.last_digital_date,DATE'2000-01-01'),
           coalesce(cg.last_congress_date,DATE'2000-01-01'), coalesce(inq.last_inquiry_date,DATE'2000-01-01')) AS last_any_engagement
FROM silver_hcp h
LEFT JOIN d USING (hcp_id) LEFT JOIN m USING (hcp_id) LEFT JOIN cg USING (hcp_id) LEFT JOIN inq USING (hcp_id);

-- HCP 360 (the unified profile + scores) ------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW gold_hcp_360
  COMMENT 'Gold: unified HCP 360 with engagement / educational-need / priority signals'
AS
WITH toptopic AS (
  SELECT hcp_id, topic_category AS top_scientific_topic, topic_interest_score AS top_topic_interest_score
  FROM (SELECT *, row_number() OVER (PARTITION BY hcp_id ORDER BY topic_interest_score DESC, mentions DESC) AS rn
        FROM gold_medical_topic_interest) WHERE rn = 1),
emerging AS (
  SELECT hcp_id, array_distinct(collect_list(topic_category)) AS emerging_topics
  FROM gold_medical_topic_interest WHERE mentions_current_30d > mentions_prior_30d GROUP BY hcp_id),
latest_note AS (
  SELECT hcp_id, information_need AS recent_question, evidence_type_requested AS recent_evidence_request,
         nullif(competitor_mentioned,'None') AS recent_competitor_interest, preferred_channel
  FROM (SELECT *, row_number() OVER (PARTITION BY hcp_id ORDER BY interaction_date DESC) AS rn
        FROM silver_msl_extracted) WHERE rn = 1),
openinq AS (SELECT hcp_id, COUNT(*) AS open_inquiries FROM silver_medical_inquiries
            WHERE response_status <> 'Closed' GROUP BY hcp_id)
SELECT
  h.hcp_id, h.hcp_name, h.specialty, h.institution, h.city, h.state, h.territory,
  h.practice_setting, h.hcp_tier, h.primary_therapeutic_area,
  h.publication_count, h.trial_participation, h.influence_score, h.npi,
  coalesce(ch.msl_interactions,0) AS msl_interactions, ch.avg_msl_duration_min AS avg_msl_duration_min,
  coalesce(ch.email_open_rate,0) AS email_open_rate, coalesce(ch.webinars_attended,0) AS webinars_attended,
  coalesce(cg.sessions_attended,0) AS congress_sessions_attended, coalesce(ch.medical_inquiries,0) AS medical_inquiries,
  coalesce(ch.channels_used,0) AS channels_used, ch.last_any_engagement,
  coalesce(mi.interactions_30d,0) AS interactions_30d, coalesce(mi.interactions_90d,0) AS interactions_90d,
  coalesce(mi.interactions_180d,0) AS interactions_180d,
  coalesce(mi.days_since_last_interaction, 999) AS days_since_last_msl,
  coalesce(mi.follow_ups_requested,0) AS follow_ups_requested,
  tt.top_scientific_topic, tt.top_topic_interest_score, em.emerging_topics,
  ln.recent_question, ln.recent_evidence_request, ln.recent_competitor_interest,
  coalesce(p.publications_tracked,0) AS publications_tracked, coalesce(p.trials_tracked,0) AS trials_tracked,
  -- scores -----------------------------------------------------------------
  ROUND(LEAST(100, coalesce(ch.email_open_rate,0)*50 + coalesce(ch.webinars_attended,0)*10
        + LEAST(coalesce(ch.webpage_clicks,0),20)*1.0), 1) AS digital_engagement_score,
  ROUND(LEAST(100, coalesce(oi.open_inquiries,0)*12 + coalesce(mi.follow_ups_requested,0)*8
        + coalesce(tt.top_topic_interest_score,0)*0.25), 1) AS educational_need_score,
  ROUND(LEAST(100, coalesce(mi.interactions_90d,0)*14 + coalesce(cg.sessions_attended,0)*8
        + coalesce(ch.email_open_rate,0)*20), 1) AS engagement_score,
  (h.influence_score >= 60 AND coalesce(mi.days_since_last_interaction,999) > 90) AS under_engaged_priority,
  ch.avg_msl_duration_min AS avg_engagement_duration,
  coalesce(ln.preferred_channel, 'In-person') AS preferred_engagement_channel,
  CASE WHEN (h.influence_score >= 60 AND coalesce(mi.days_since_last_interaction,999) > 90)
         OR coalesce(oi.open_inquiries,0) > 0 THEN 'Within 14 days'
       WHEN coalesce(mi.days_since_last_interaction,999) > 60 THEN 'Within 30 days'
       ELSE 'Within 60 days' END AS recommended_follow_up_window
FROM silver_hcp h
LEFT JOIN gold_hcp_channel_engagement ch USING (hcp_id)
LEFT JOIN gold_msl_interaction_summary mi USING (hcp_id)
LEFT JOIN gold_congress_engagement cg USING (hcp_id)
LEFT JOIN toptopic tt USING (hcp_id)
LEFT JOIN emerging em USING (hcp_id)
LEFT JOIN latest_note ln USING (hcp_id)
LEFT JOIN openinq oi USING (hcp_id)
LEFT JOIN (SELECT hcp_id, COUNT(CASE WHEN record_type='Publication' THEN 1 END) AS publications_tracked,
                  COUNT(CASE WHEN record_type='Clinical Trial' THEN 1 END) AS trials_tracked
           FROM silver_publications GROUP BY hcp_id) p USING (hcp_id);

-- HCP priority (MSL action ranking) -----------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW gold_hcp_priority
  COMMENT 'Gold: MSL priority ranking (feeds Lakebase operational serving)'
AS
SELECT hcp_id, hcp_name, specialty, territory, hcp_tier, primary_therapeutic_area,
  influence_score, engagement_score, educational_need_score, digital_engagement_score,
  under_engaged_priority, days_since_last_msl, follow_ups_requested,
  top_scientific_topic, top_topic_interest_score, recent_competitor_interest,
  ROUND(influence_score*0.40 + educational_need_score*0.35 + (100 - engagement_score)*0.25, 1) AS msl_priority_score,
  CASE WHEN engagement_score >= 60 THEN 'Highly Engaged'
       WHEN engagement_score >= 30 THEN 'Moderately Engaged'
       ELSE 'Under-Engaged' END AS engagement_segment,
  CASE WHEN ROUND(influence_score*0.40 + educational_need_score*0.35 + (100 - engagement_score)*0.25, 1) >= 65 THEN 'High'
       WHEN ROUND(influence_score*0.40 + educational_need_score*0.35 + (100 - engagement_score)*0.25, 1) >= 45 THEN 'Medium'
       ELSE 'Low' END AS priority_tier
FROM gold_hcp_360;

-- Next-best-engagement recommendation ---------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW gold_next_best_engagement
  COMMENT 'Gold: next-best-engagement recommendation per HCP (synced to Lakebase)'
AS
WITH ov AS (SELECT hcp_id, COUNT(CASE WHEN overdue THEN 1 END) AS overdue_inq
            FROM silver_medical_inquiries GROUP BY hcp_id)
SELECT p.hcp_id, p.hcp_name, p.specialty, p.territory, p.priority_tier, p.msl_priority_score, p.engagement_segment,
  CASE WHEN coalesce(ov.overdue_inq,0) > 0 THEN 'Open medical inquiry overdue'
       WHEN t.under_engaged_priority THEN 'High-influence KOL under-engaged'
       WHEN p.follow_ups_requested > 0 THEN 'Outstanding MSL follow-up requested'
       WHEN p.recent_competitor_interest IS NOT NULL THEN 'Competitive scientific interest expressed'
       ELSE 'Scientific engagement cadence' END AS trigger,
  coalesce(p.top_scientific_topic, 'General Scientific Exchange') AS topic,
  concat('Address ', coalesce(t.recent_question, 'outstanding scientific question'),
         ' with approved evidence on ', coalesce(p.top_scientific_topic, 'the portfolio')) AS suggested_engagement,
  concat(t.preferred_engagement_channel, ' · ', coalesce(p.top_scientific_topic, 'Scientific exchange')) AS suggested_channel_topic,
  CASE WHEN t.recommended_follow_up_window = 'Within 14 days' THEN date_add(current_date(), 14)
       WHEN t.recommended_follow_up_window = 'Within 30 days' THEN date_add(current_date(), 30)
       ELSE date_add(current_date(), 60) END AS recommended_date,
  (coalesce(ov.overdue_inq,0) > 0) AS overdue,
  'Pending MSL review' AS review_status
FROM gold_hcp_priority p
LEFT JOIN gold_hcp_360 t USING (hcp_id)
LEFT JOIN ov USING (hcp_id);

-- Territory opportunity -----------------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW gold_territory_opportunity
  COMMENT 'Gold: per-territory reach & opportunity'
AS
WITH cl AS (SELECT territory, SUM(diagnosed_patient_count) AS diagnosed_patients,
              SUM(treated_patient_count) AS treated_patients,
              ROUND(AVG(treatment_penetration_rate),2) AS avg_treatment_penetration
            FROM silver_claims GROUP BY territory)
SELECT h.territory,
  COUNT(DISTINCT h.hcp_id) AS total_hcps,
  COUNT(DISTINCT CASE WHEN pr.priority_tier='High' THEN h.hcp_id END) AS priority_hcps,
  COUNT(DISTINCT CASE WHEN h.days_since_last_msl <= 90 THEN h.hcp_id END) AS engaged_90d,
  COUNT(DISTINCT CASE WHEN h.under_engaged_priority THEN h.hcp_id END) AS under_engaged_priority_hcps,
  ROUND(COUNT(DISTINCT CASE WHEN h.days_since_last_msl <= 90 THEN h.hcp_id END)*100.0
        / NULLIF(COUNT(DISTINCT h.hcp_id),0), 1) AS reach_rate,
  ROUND(AVG(h.engagement_score),1) AS avg_engagement_score,
  ROUND(AVG(h.educational_need_score),1) AS avg_educational_need,
  coalesce(cl.diagnosed_patients,0) AS diagnosed_patients, coalesce(cl.treated_patients,0) AS treated_patients,
  coalesce(cl.avg_treatment_penetration,0) AS avg_treatment_penetration,
  ROUND(COUNT(DISTINCT CASE WHEN h.under_engaged_priority THEN h.hcp_id END)*2
        + AVG(h.educational_need_score)*0.5, 1) AS territory_opportunity_score
FROM gold_hcp_360 h
LEFT JOIN gold_hcp_priority pr USING (hcp_id)
LEFT JOIN cl ON cl.territory = h.territory
GROUP BY h.territory, cl.diagnosed_patients, cl.treated_patients, cl.avg_treatment_penetration;
