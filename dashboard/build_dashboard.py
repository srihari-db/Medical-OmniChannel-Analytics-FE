"""Build the AI/BI dashboard JSON for Medical Omnichannel Intelligence (Daiichi).
Emits dashboard/medical_omnichannel_intelligence.lvdash.json. All dataset queries
were validated via execute_sql before building (see evidence/10)."""
import json

C = "`_sa701`.moa"  # note: dataset SQL uses backticked catalog


def txt(name, md, x, y, w, h):
    return {"widget": {"name": name, "multilineTextboxSpec": {"lines": [md]}},
            "position": {"x": x, "y": y, "width": w, "height": h}}


def counter(name, ds, field, title, x, y, disagg=True):
    return {"widget": {"name": name, "queries": [{"name": "main_query", "query": {
        "datasetName": ds, "fields": [{"name": field, "expression": f"`{field}`"}],
        "disaggregated": disagg}}],
        "spec": {"version": 2, "widgetType": "counter",
                 "encodings": {"value": {"fieldName": field, "displayName": title}},
                 "frame": {"showTitle": True, "title": title}}},
        "position": {"x": x, "y": y, "width": 2, "height": 3}}


def bar(name, ds, xf, yf, xlab, ylab, title, x, y, w=3, h=5, color=None):
    fields = [{"name": xf, "expression": f"`{xf}`"}, {"name": yf, "expression": f"`{yf}`"}]
    enc = {"x": {"fieldName": xf, "scale": {"type": "categorical"}, "displayName": xlab},
           "y": {"fieldName": yf, "scale": {"type": "quantitative"}, "displayName": ylab}}
    if color:
        fields.append({"name": color, "expression": f"`{color}`"})
        enc["color"] = {"fieldName": color, "scale": {"type": "categorical"}, "displayName": color}
    return {"widget": {"name": name, "queries": [{"name": "main_query", "query": {
        "datasetName": ds, "fields": fields, "disaggregated": True}}],
        "spec": {"version": 3, "widgetType": "bar", "encodings": enc,
                 "frame": {"showTitle": True, "title": title}}},
        "position": {"x": x, "y": y, "width": w, "height": h}}


def pie(name, ds, angle, color, title, x, y, w=3, h=5):
    return {"widget": {"name": name, "queries": [{"name": "main_query", "query": {
        "datasetName": ds, "fields": [{"name": angle, "expression": f"`{angle}`"},
                                      {"name": color, "expression": f"`{color}`"}],
        "disaggregated": True}}],
        "spec": {"version": 3, "widgetType": "pie",
                 "encodings": {"angle": {"fieldName": angle, "scale": {"type": "quantitative"}, "displayName": angle},
                               "color": {"fieldName": color, "scale": {"type": "categorical"}, "displayName": color}},
                 "frame": {"showTitle": True, "title": title}}},
        "position": {"x": x, "y": y, "width": w, "height": h}}


def table(name, ds, cols, title, x, y, w=6, h=6):
    fields = [{"name": c[0], "expression": f"`{c[0]}`"} for c in cols]
    columns = [{"fieldName": c[0], "displayName": c[1]} for c in cols]
    return {"widget": {"name": name, "queries": [{"name": "main_query", "query": {
        "datasetName": ds, "fields": fields, "disaggregated": True}}],
        "spec": {"version": 2, "widgetType": "table", "encodings": {"columns": columns},
                 "frame": {"showTitle": True, "title": title}}},
        "position": {"x": x, "y": y, "width": w, "height": h}}


dashboard = {
    "datasets": [
        {"name": "kpis", "displayName": "Headline KPIs", "queryLines": [
            f"SELECT (SELECT COUNT(*) FROM {C}.gold_hcp_360) AS total_hcps, ",
            f"(SELECT COUNT(*) FROM {C}.gold_hcp_priority WHERE priority_tier='High') AS priority_high, ",
            f"(SELECT ROUND(COUNT_IF(days_since_last_msl<=90)/COUNT(*),3) FROM {C}.gold_hcp_360) AS reach_90d_pct, ",
            f"(SELECT COUNT_IF(under_engaged_priority) FROM {C}.gold_hcp_360) AS under_engaged, ",
            f"(SELECT COUNT_IF(overdue) FROM {C}.gold_medical_information_requests) AS overdue_inquiries, ",
            f"(SELECT ROUND(AVG(response_time_days),1) FROM {C}.gold_medical_information_requests WHERE response_status='Closed') AS avg_response_days"]},
        {"name": "reach_by_territory", "displayName": "Reach by territory", "queryLines": [
            f"SELECT territory, total_hcps, reach_rate, under_engaged_priority_hcps, ",
            f"ROUND(territory_opportunity_score,1) AS opportunity_score ",
            f"FROM {C}.gold_territory_opportunity ORDER BY reach_rate ASC"]},
        {"name": "topic_interest", "displayName": "Scientific topic interest", "queryLines": [
            f"SELECT topic_category, SUM(mentions) AS mentions, COUNT(DISTINCT hcp_id) AS hcps ",
            f"FROM {C}.gold_medical_topic_interest GROUP BY topic_category ORDER BY mentions DESC"]},
        {"name": "inquiry_sla", "displayName": "Medical inquiry SLA by product", "queryLines": [
            f"SELECT product, COUNT(*) AS total_inquiries, COUNT_IF(overdue) AS overdue_inquiries, ",
            f"ROUND(COUNT_IF(sla_met)/NULLIF(COUNT_IF(response_status='Closed'),0),3) AS sla_met_pct ",
            f"FROM {C}.gold_medical_information_requests GROUP BY product ORDER BY total_inquiries DESC"]},
        {"name": "priority_dist", "displayName": "Priority tier distribution", "queryLines": [
            f"SELECT priority_tier, COUNT(*) AS hcps FROM {C}.gold_hcp_priority GROUP BY priority_tier"]},
        {"name": "next_best_queue", "displayName": "MSL next-best-engagement queue", "queryLines": [
            f"SELECT hcp_name, territory, priority_tier, ROUND(msl_priority_score,1) AS msl_priority_score, ",
            f"trigger, topic, recommended_date FROM {C}.gold_next_best_engagement ",
            f"ORDER BY msl_priority_score DESC LIMIT 25"]},
    ],
    "pages": [{
        "name": "overview", "displayName": "Medical Omnichannel Intelligence",
        "pageType": "PAGE_TYPE_CANVAS",
        "layout": [
            txt("title", "## Medical Omnichannel Intelligence — Daiichi Sankyo (Oncology Medical Affairs)", 0, 0, 6, 1),
            txt("subtitle", "MSL engagement, scientific interest & medical-inquiry SLAs across the portfolio. Synthetic, non-promotional demo data.", 0, 1, 6, 1),
            counter("kpi-total-hcps", "kpis", "total_hcps", "Total HCPs", 0, 2),
            counter("kpi-reach", "kpis", "reach_90d_pct", "90-day HCP reach", 2, 2),
            counter("kpi-underengaged", "kpis", "under_engaged", "Under-engaged priority KOLs", 4, 2),
            counter("kpi-priority-high", "kpis", "priority_high", "High-priority KOLs", 0, 5),
            counter("kpi-overdue", "kpis", "overdue_inquiries", "Overdue medical inquiries", 2, 5),
            counter("kpi-response", "kpis", "avg_response_days", "Avg inquiry response (days)", 4, 5),
            txt("sec-reach", "### Engagement & reach", 0, 8, 6, 1),
            bar("bar-territory", "reach_by_territory", "territory", "reach_rate",
                "Territory", "90-day reach %", "90-day HCP reach by territory", 0, 9, 3, 5),
            pie("pie-priority", "priority_dist", "hcps", "priority_tier", "HCPs by MSL priority tier", 3, 9, 3, 5),
            txt("sec-sci", "### Scientific interest & medical inquiries", 0, 14, 6, 1),
            bar("bar-topics", "topic_interest", "topic_category", "mentions",
                "Topic", "Mentions", "Scientific topic interest (mentions)", 0, 15, 3, 5),
            bar("bar-sla", "inquiry_sla", "product", "overdue_inquiries",
                "Product", "Overdue inquiries", "Overdue medical inquiries by product", 3, 15, 3, 5),
            txt("sec-queue", "### MSL next-best-engagement queue", 0, 20, 6, 1),
            table("tbl-queue", "next_best_queue",
                  [("hcp_name", "HCP"), ("territory", "Territory"), ("priority_tier", "Priority"),
                   ("msl_priority_score", "Score"), ("trigger", "Trigger"), ("topic", "Topic"),
                   ("recommended_date", "Recommended by")],
                  "MSL next-best-engagement queue (top 25)", 0, 21, 6, 7),
        ]}]
}

out = "/Users/srihari.a/febar/Medical-OmniChannel-Analytics-FE/dashboard/medical_omnichannel_intelligence.lvdash.json"
with open(out, "w") as f:
    json.dump(dashboard, f, indent=2)
print("wrote", out)
