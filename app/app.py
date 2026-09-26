"""Medical Engagement Copilot — Daiichi Sankyo oncology Medical Affairs (FE BAR demo).

Integrated data journey surfaced to the business:
  Lakeflow -> Unity Catalog (Gold) -> Lakebase (operational queue + write-back)
  -> Gen AI briefing (ai_query) -> Genie (NL Q&A) -> this app.

Two views:
  1. MSL Action Queue   — low-latency next-best-engagement served from Lakebase
  2. HCP Pre-Engagement — unified 360 + AI briefing + governed content + write-back

All recommendations require MSL review. Data is synthetic.
"""
import datetime
import streamlit as st
import backend as be

st.set_page_config(page_title="Medical Engagement Copilot", page_icon="🧬", layout="wide")

st.markdown("""
<style>
  .block-container {padding-top: 2rem; max-width: 1350px;}
  .mec-card {background:#F7F9FC; border:1px solid #E3E8EF; border-radius:12px; padding:16px 18px; margin-bottom:12px;}
  .mec-brief {background:#EEF4FF; border-left:5px solid #2D5BFF; border-radius:8px; padding:16px 20px; font-size:1.02rem; line-height:1.5;}
  .mec-plan {background:#F3FBF4; border-left:5px solid #1F9D55; border-radius:8px; padding:16px 20px;}
  .mec-gov {background:#FFF8ED; border-left:5px solid #D9822B; border-radius:8px; padding:12px 16px; font-size:0.9rem;}
  .mec-lake {background:#F0F7FF; border-left:5px solid #0B6BCB; border-radius:8px; padding:10px 14px; font-size:0.85rem;}
  .mec-pill {display:inline-block; padding:2px 10px; border-radius:12px; font-size:0.78rem; font-weight:600; margin-right:6px;}
  .pill-high {background:#FDE4E1; color:#B4231A;} .pill-med {background:#FEF3CD; color:#8A6100;} .pill-low {background:#E1ECFB; color:#1F5199;}
  h1 {font-size:1.9rem;} .mec-label {color:#5A6472; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.04em;}
</style>
""", unsafe_allow_html=True)

st.title("🧬 Medical Engagement Copilot")
st.caption("Daiichi Sankyo oncology Medical Affairs · unified HCP 360 + Gen AI + Lakebase operational serving · "
           "**all recommendations require MSL review** · synthetic demo data")


def pill(tier):
    t = (tier or "").lower()
    cls = "pill-high" if "high" in t else "pill-med" if "medium" in t else "pill-low"
    return f'<span class="mec-pill {cls}">{tier}</span>'


def fmt_date(d):
    if d is None:
        return "—"
    if isinstance(d, (datetime.date, datetime.datetime)):
        return d.strftime("%Y-%m-%d")
    return str(d)


try:
    hcps = be.list_hcps()
except Exception as e:
    st.error(f"Could not load HCP list — check the app's SQL warehouse resource.\n\n{e}")
    st.stop()

hcp_by_label = {f"{h['hcp_name']} — {h['specialty']} ({h['territory']}) · priority {h['msl_priority_score']:.0f}": h
                for h in hcps}

tab_queue, tab_detail = st.tabs(["📋 MSL Action Queue (Lakebase)", "🔬 HCP Pre-Engagement Briefing"])

# =========================================================== ACTION QUEUE ===
with tab_queue:
    st.subheader("Next-best-engagement queue — served from Lakebase")
    st.markdown('<div class="mec-lake">⚡ <b>Operational serving:</b> this queue is read from the '
                '<b>Lakebase</b> PostgreSQL table <code>public.msl_action_queue</code>, kept in sync with the '
                'governed Gold table <code>_sa701.moa.serving_msl_action_queue</code> via reverse ETL. '
                'Point lookups return in milliseconds — suitable for an operational MSL cockpit.</div>',
                unsafe_allow_html=True)
    try:
        queue = be.lakebase_action_queue(limit=50)
        st.dataframe(
            [{"HCP": q["hcp_name"], "Specialty": q["specialty"], "Territory": q["territory"],
              "Priority": q["priority_tier"], "Score": round(q["msl_priority_score"], 1),
              "Trigger": q["trigger"], "Topic": q["topic"],
              "Recommended by": fmt_date(q["recommended_date"]), "Overdue": "⚠️" if q["overdue"] else ""}
             for q in queue],
            hide_index=True, use_container_width=True, height=520)
        st.caption(f"{len(queue)} HCPs in the operational queue · sorted by MSL priority score")
    except Exception as e:
        st.warning(f"Lakebase queue unavailable (check the app's database resource): {e}")

# =========================================================== HCP DETAIL =====
with tab_detail:
    with st.sidebar:
        st.header("Select HCP")
        st.caption(f"{len(hcps)} HCPs · sorted by MSL priority score")
        choice = st.selectbox("Healthcare Professional", list(hcp_by_label.keys()))
        selected = hcp_by_label[choice]
        hcp_id = selected["hcp_id"]
        st.markdown(f"**{selected['hcp_name']}**")
        st.markdown(pill(selected["priority_tier"]), unsafe_allow_html=True)
        gen = st.button("🧠 Generate AI briefing", type="primary", use_container_width=True)

    profile = be.get_profile(hcp_id)
    interactions = be.get_recent_interactions(hcp_id)
    topics = be.get_topic_interests(hcp_id)
    inquiries = be.get_inquiries(hcp_id)
    congress = be.get_congress(hcp_id)
    pubs = be.get_publications(hcp_id)
    shared = be.get_content_shared(hcp_id)
    nbe = be.get_next_best(hcp_id)
    rec = be.recommend_content(hcp_id)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Influence Score", f"{profile.get('influence_score', 0):.0f}")
    c2.metric("Engagement Score", f"{profile.get('engagement_score', 0):.0f}")
    c3.metric("Educational Need", f"{profile.get('educational_need_score', 0):.0f}")
    days = profile.get("days_since_last_msl", 999)
    c4.metric("Days Since Last MSL", "—" if days == 999 else f"{days:.0f}")

    st.subheader("AI-generated pre-engagement briefing")

    def build_context():
        lines = [
            f"HCP: {profile['hcp_name']}, {profile['specialty']}, {profile['practice_setting']} setting.",
            f"Institution: {profile['institution']} ({profile['city']}, {profile['state']}, {profile['territory']}).",
            f"Tier: {profile['hcp_tier']}. Influence {profile.get('influence_score',0)}, "
            f"publications {profile.get('publication_count',0)}, trials {profile.get('trial_participation',0)}.",
            f"Engagement: {profile.get('msl_interactions',0)} MSL interactions; "
            f"{profile.get('interactions_90d',0)} in last 90 days; "
            f"last MSL {'never' if days==999 else str(int(days))+' days ago'}.",
        ]
        if topics:
            lines.append("Top scientific interests: " + ", ".join(
                f"{t['topic_category']} (score {t['topic_interest_score']:.0f})" for t in topics[:4]) + ".")
        if profile.get("emerging_topics"):
            lines.append(f"Emerging interest topics: {profile.get('emerging_topics')}.")
        if interactions:
            i = interactions[0]
            lines.append(f"Most recent MSL note ({fmt_date(i['interaction_date'])}, {i['channel']}): "
                         f"topic '{i['scientific_topic']}', need '{i['information_need']}', "
                         f"sentiment {i['sentiment']}, interest {i['interest_level']}, "
                         f"follow-up requested: {i['follow_up_requested']}, evidence: {i['evidence_type_requested']}"
                         + (f", competitor: {i['competitor_mentioned']}"
                            if i.get('competitor_mentioned') and i['competitor_mentioned'] != 'None' else "") + ".")
        open_inq = [q for q in inquiries if q['response_status'] != 'Closed']
        if open_inq:
            lines.append("Open medical inquiries: " + "; ".join(
                f"{q['inquiry_topic']} ({q['indication']})" for q in open_inq[:3]) + ".")
        lines.append(f"Outstanding follow-ups requested: {profile.get('follow_ups_requested',0)}.")
        return "\n".join(lines)

    if gen:
        with st.spinner("Generating briefing with ai_query on the Databricks LLM endpoint…"):
            try:
                st.session_state[f"brief_{hcp_id}"] = be.generate_briefing(build_context())
            except Exception as e:
                st.error(f"Briefing generation failed: {e}")

    brief = st.session_state.get(f"brief_{hcp_id}")
    if brief:
        st.markdown(f'<div class="mec-brief">{brief}</div>', unsafe_allow_html=True)
    else:
        st.info("Click **Generate AI briefing** in the sidebar to produce the narrative for this HCP.")

    st.subheader("Suggested engagement plan")
    pc1, pc2 = st.columns([3, 2])
    with pc1:
        topic = (nbe or {}).get("topic") or (topics[0]['topic_category'] if topics else "Scientific exchange")
        trigger = (nbe or {}).get("trigger") or "Scientific engagement cadence"
        channel = profile.get("preferred_engagement_channel", "In-person")
        timing = profile.get("recommended_follow_up_window", "Within 30 days")
        asset = rec['content_title'] if rec else "MSL to identify approved asset"
        objective = (nbe or {}).get("suggested_engagement") or "Address outstanding scientific question"
        st.markdown(f"""
<div class="mec-plan">
<b>Objective:</b> {objective}<br><b>Trigger:</b> {trigger}<br><b>Topic:</b> {topic}<br>
<b>Supporting asset:</b> {asset}<br><b>Preferred channel:</b> {channel}<br>
<b>Timing:</b> {timing}<br><b>Required review:</b> MSL confirmation
</div>""", unsafe_allow_html=True)
    with pc2:
        if rec:
            st.markdown(f"""
<div class="mec-card"><div class="mec-label">Recommended approved content</div>
<b>{rec['content_title']}</b><br>
<span class="mec-label">Type</span> {rec['content_type']} · <span class="mec-label">Topic</span> {rec['topic_category']}<br>
<span class="mec-label">Indication</span> {rec['indication']} · <span class="mec-label">Product</span> {rec['product']}<br>
<span class="mec-label">Status</span> ✅ {rec['approval_status']} · <span class="mec-label">Med review</span> {rec['med_review_id']}
</div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="mec-card">No unshared approved asset matched the top interest — '
                        'MSL to select content.</div>', unsafe_allow_html=True)

    # ---- Lakebase write-back: MSL logs a review decision ------------------
    st.markdown("**✍️ Log MSL review decision (writes back to Lakebase)**")
    with st.form(f"review_{hcp_id}"):
        rc1, rc2, rc3 = st.columns(3)
        decision = rc1.selectbox("Decision", ["Approved", "Deferred", "Rejected"])
        channel_sel = rc2.selectbox("Channel", ["In-person", "Virtual", "Phone", "Congress", "Email"])
        sched = rc3.date_input("Scheduled date", value=datetime.date.today() + datetime.timedelta(days=14))
        notes = st.text_input("Review notes", value=f"Reviewed next-best-engagement for {profile['hcp_name']}.")
        submitted = st.form_submit_button("Save decision to Lakebase", type="primary")
        if submitted:
            try:
                be.lakebase_record_review(hcp_id, "Dr. Amara Osei", decision, notes, channel_sel, str(sched))
                st.success("Saved to Lakebase (public.msl_review_actions). Operational write-back complete.")
            except Exception as e:
                st.error(f"Write-back failed: {e}")
    try:
        prior = be.lakebase_recent_reviews(hcp_id)
        if prior:
            st.caption("Recent review actions for this HCP (from Lakebase):")
            st.dataframe([{"Decision": p["review_decision"], "Channel": p["scheduled_channel"],
                           "Scheduled": fmt_date(p["scheduled_date"]), "Notes": p["review_notes"]} for p in prior],
                         hide_index=True, use_container_width=True)
    except Exception:
        pass

    st.markdown('<div class="mec-gov">🔒 <b>Governance:</b> Recommendations are derived from the HCP\'s own MSL notes, '
                'medical inquiries, congress and topic-interest signals, and only surface <b>medically approved</b> '
                'content (with review ID). This is a recommendation for MSL review — not an automated or promotional action.</div>',
                unsafe_allow_html=True)

    st.divider()
    st.subheader("Supporting evidence — HCP 360")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Profile**")
        st.markdown(f"""<div class="mec-card">{profile['hcp_name']} · {profile['specialty']}<br>
{profile['institution']}<br>{profile['city']}, {profile['state']} · {profile['territory']} · {profile['practice_setting']}<br>
{pill(profile['hcp_tier'])} Influence {profile.get('influence_score',0):.0f} ·
Pubs {profile.get('publication_count',0)} · Trials {profile.get('trial_participation',0)}</div>""",
                    unsafe_allow_html=True)
        st.markdown("**Top scientific interests**")
        if topics:
            st.dataframe([{"Topic": t["topic_category"], "Interest": round(t["topic_interest_score"]),
                           "Mentions": t["mentions"], "30d vs prior": (t["mentions_current_30d"] - t["mentions_prior_30d"])}
                          for t in topics], hide_index=True, use_container_width=True)
        st.markdown("**Recent medical inquiries**")
        if inquiries:
            st.dataframe([{"Date": fmt_date(q["inquiry_date"]), "Topic": q["inquiry_topic"],
                           "Indication": q["indication"], "Status": q["response_status"],
                           "Overdue": "⚠️" if q["overdue"] else ""} for q in inquiries],
                         hide_index=True, use_container_width=True)
    with col_b:
        st.markdown("**Recent MSL interactions**")
        if interactions:
            st.dataframe([{"Date": fmt_date(i["interaction_date"]), "Channel": i["channel"],
                           "Topic": i["topic_category"], "Sentiment": i["sentiment"],
                           "Follow-up": "✅" if i["follow_up_requested"] else "—"} for i in interactions],
                         hide_index=True, use_container_width=True)
        st.markdown("**Congress participation**")
        if congress and congress.get("sessions_attended"):
            st.markdown(f"""<div class="mec-card">Sessions attended: <b>{congress['sessions_attended']}</b> ·
Events: {congress['distinct_events']} · Booth visits: {congress['booth_visits']}<br>
Last congress: {fmt_date(congress['last_congress_date'])}</div>""", unsafe_allow_html=True)
        st.markdown("**Publications & clinical trials**")
        if pubs:
            st.dataframe([{"Type": p["record_type"], "Title": p["title"], "Year": p["year"],
                           "Venue": p["journal_or_registry"]} for p in pubs], hide_index=True, use_container_width=True)

st.caption("Medical Omnichannel Intelligence · Daiichi Sankyo demo · _sa701.moa + Lakebase · synthetic data")
