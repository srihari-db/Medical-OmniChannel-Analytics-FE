"""Synthetic data generator — Daiichi Sankyo Medical Omnichannel Intelligence (FE BAR).

Generates internally-consistent SYNTHETIC Medical Affairs data for a Daiichi Sankyo
oncology context (Enhertu / trastuzumab deruxtecan, Datroway / datopotamab deruxtecan
and pipeline ADCs). NO real customer / patient / HCP data is used — every name,
institution and note is fabricated.

Outputs one CSV per raw dataset into ./ (or --out DIR). Each raw dataset carries
~250-500 rows, feeding the Bronze layer of the Lakeflow medallion pipeline.

Datasets:
  hcp_master              ~300  oncology HCPs / KOLs
  msl_interactions        ~500  MSL field engagements w/ free-text raw_notes (GenAI input)
  medical_inquiries       ~400  medical information requests + SLA
  congress_events         ~420  congress / session attendance
  digital_engagement      ~500  email / webinar / web activity
  publications_trials     ~350  publications & trial participation
  patient_claims_summary  ~300  de-identified territory epidemiology (synthetic)
  approved_content         ~70  medically-approved content catalog
  content_shared          ~320  approved content shared with HCPs

Usage:  python generate_synthetic_data.py --out ../data/raw
"""
import argparse
import csv
import os
import random
from datetime import date, timedelta

SEED = 20260926
random.seed(SEED)

TODAY = date(2026, 9, 26)

# --------------------------------------------------------------------------- #
# Reference vocabularies — Daiichi Sankyo oncology Medical Affairs context
# --------------------------------------------------------------------------- #
PRODUCTS = {
    "Enhertu": {
        "inn": "trastuzumab deruxtecan (T-DXd)",
        "indications": [
            "HER2+ metastatic breast cancer",
            "HER2-low metastatic breast cancer",
            "HER2-ultralow metastatic breast cancer",
            "HER2+ metastatic gastric cancer",
            "HER2-mutant metastatic NSCLC",
        ],
        "ta": "Oncology",
    },
    "Datroway": {
        "inn": "datopotamab deruxtecan (Dato-DXd)",
        "indications": [
            "HR+/HER2- metastatic breast cancer",
            "TROP2 metastatic NSCLC",
        ],
        "ta": "Oncology",
    },
    "HER3-DXd": {
        "inn": "patritumab deruxtecan (pipeline)",
        "indications": ["EGFR-mutant NSCLC (investigational)"],
        "ta": "Oncology",
    },
    "Vanflyta": {
        "inn": "quizartinib",
        "indications": ["FLT3-ITD+ acute myeloid leukemia"],
        "ta": "Hematology-Oncology",
    },
}
PRODUCT_NAMES = list(PRODUCTS.keys())

# Scientific topics MSLs discuss; each maps to a topic_category bucket used downstream.
TOPIC_LIBRARY = [
    ("interstitial lung disease / pneumonitis monitoring and management", "Safety / ILD Management"),
    ("ADC-related ILD adverse event grading and dose interruption", "Safety / ILD Management"),
    ("nausea and dosing management for antibody-drug conjugates", "Dosing & Administration"),
    ("HER2 IHC testing and HER2-low patient identification", "Biomarker & Patient Selection"),
    ("HER2-ultralow diagnostic thresholds and assay standardization", "Biomarker & Patient Selection"),
    ("TROP2 expression and biomarker-driven patient selection", "Biomarker & Patient Selection"),
    ("real-world evidence for T-DXd in HER2-low populations", "Real-World Evidence"),
    ("real-world outcomes and treatment patterns post-T-DXd", "Real-World Evidence"),
    ("long-term duration of response and survival outcomes", "Long-term Efficacy & Outcomes"),
    ("DESTINY-Breast04 and DESTINY-Breast06 efficacy data", "Long-term Efficacy & Outcomes"),
    ("CNS activity and brain metastases outcomes", "CNS / Brain Metastases"),
    ("intracranial response in patients with brain metastases", "CNS / Brain Metastases"),
    ("optimal sequencing after T-DXd progression", "Sequencing & Combinations"),
    ("combination strategies with immunotherapy", "Sequencing & Combinations"),
    ("comparative evidence versus T-DM1 and trastuzumab", "Comparative Evidence"),
    ("head-to-head data and comparative effectiveness", "Comparative Evidence"),
    ("TROPION-Lung and TROPION-Breast trial design", "Long-term Efficacy & Outcomes"),
    ("general scientific exchange on the oncology portfolio", "General Scientific Exchange"),
]

COMPETITORS = ["Kadcyla", "Trodelvy", "Perjeta", "Phesgo", "Tukysa", "None", "None", "None"]

INFO_NEEDS = [
    "Requested peer-reviewed publications", "Asked for congress data / abstracts",
    "Requested subgroup analysis", "Wants safety management guidance",
    "Requested clinical trial enrollment info", "Asked for dosing schedule details",
    "Requested comparative efficacy data", "Wants real-world evidence data",
    "Requested biomarker testing guidance", "Asked about mechanism of action",
]
EVIDENCE_TYPES = ["Efficacy", "Safety", "Real-World Evidence", "Comparative", "Mechanism of Action",
                  "Subgroup Analysis", "Dosing", "Biomarker"]
SENTIMENTS = ["Positive", "Positive", "Neutral", "Neutral", "Negative"]
INTEREST = ["High", "High", "Medium", "Medium", "Low"]
CHANNELS = ["In-person", "Virtual", "Phone", "Congress", "Email"]

SPECIALTIES = ["Medical Oncology", "Hematology-Oncology", "Breast Oncology", "Thoracic Oncology",
               "Gastrointestinal Oncology", "Radiation Oncology", "Pathology"]
PRACTICE_SETTINGS = ["Academic Medical Center", "Community Oncology", "NCI-Designated Cancer Center",
                     "Integrated Health System", "Private Practice"]
TIERS = ["Tier 1 KOL", "Tier 2", "Tier 3"]

INSTITUTIONS = [
    ("Memorial Sloan Kettering", "New York", "NY", "Northeast"),
    ("Dana-Farber Cancer Institute", "Boston", "MA", "Northeast"),
    ("MD Anderson Cancer Center", "Houston", "TX", "South"),
    ("Mayo Clinic", "Rochester", "MN", "Midwest"),
    ("Cleveland Clinic Taussig", "Cleveland", "OH", "Midwest"),
    ("Stanford Cancer Institute", "Palo Alto", "CA", "West"),
    ("UCLA Jonsson Cancer Center", "Los Angeles", "CA", "West"),
    ("UCSF Helen Diller", "San Francisco", "CA", "West"),
    ("Johns Hopkins Sidney Kimmel", "Baltimore", "MD", "Northeast"),
    ("Northwestern Lurie", "Chicago", "IL", "Midwest"),
    ("Duke Cancer Institute", "Durham", "NC", "South"),
    ("Winship Cancer Institute (Emory)", "Atlanta", "GA", "South"),
    ("Fred Hutchinson", "Seattle", "WA", "West"),
    ("Moffitt Cancer Center", "Tampa", "FL", "South"),
    ("City of Hope", "Duarte", "CA", "West"),
    ("Vanderbilt-Ingram", "Nashville", "TN", "South"),
    ("University of Michigan Rogel", "Ann Arbor", "MI", "Midwest"),
    ("Yale Cancer Center", "New Haven", "CT", "Northeast"),
    ("UPMC Hillman", "Pittsburgh", "PA", "Northeast"),
    ("Huntsman Cancer Institute", "Salt Lake City", "UT", "West"),
]
TERRITORY_BY_REGION = {
    "Northeast": ["NE-01", "NE-02", "NE-03"],
    "South": ["SO-01", "SO-02", "SO-03"],
    "Midwest": ["MW-01", "MW-02"],
    "West": ["WE-01", "WE-02", "WE-03"],
}

FIRST_NAMES = ["Sarah", "James", "Priya", "Michael", "Elena", "David", "Aisha", "Robert", "Mei",
               "Carlos", "Anna", "John", "Fatima", "William", "Sofia", "Daniel", "Ling", "Thomas",
               "Rachel", "Ahmed", "Laura", "Kevin", "Nina", "Paul", "Yuki", "Grace", "Omar",
               "Julia", "Steven", "Maria", "Raj", "Hannah", "George", "Leila", "Peter", "Chloe"]
LAST_NAMES = ["Chen", "Patel", "Rodriguez", "Kim", "Johnson", "Nguyen", "Smith", "Garcia", "Lee",
              "Williams", "Okafor", "Brown", "Tanaka", "Martinez", "Singh", "Davis", "Wong",
              "Muller", "Rossi", "Cohen", "Ali", "Anderson", "Yamamoto", "Ivanova", "Khan",
              "Silva", "Schmidt", "Dubois", "Novak", "Reyes", "Andersson", "Petrov", "Costa"]
MSL_NAMES = ["Dr. Amara Osei", "Dr. Ben Carrington", "Dr. Clara Winters", "Dr. Devin Rao",
             "Dr. Elise Fournier", "Dr. Farid Nazari", "Dr. Grace Lim", "Dr. Henry Kwon"]

CONGRESS_EVENTS = [
    ("ASCO Annual Meeting 2026", "West", date(2026, 6, 1)),
    ("ESMO Congress 2025", "Northeast", date(2025, 10, 17)),
    ("San Antonio Breast Cancer Symposium 2025", "South", date(2025, 12, 9)),
    ("ASCO GI 2026", "West", date(2026, 1, 18)),
    ("AACR Annual Meeting 2026", "South", date(2026, 4, 25)),
    ("ASH Annual Meeting 2025", "West", date(2025, 12, 6)),
    ("World Conference on Lung Cancer 2025", "Midwest", date(2025, 9, 6)),
]

# --------------------------------------------------------------------------- #
def rid(prefix, i):
    return f"{prefix}-{i:05d}"


def rand_date(start, end):
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 0)))


def write_csv(out_dir, name, header, rows):
    path = os.path.join(out_dir, f"{name}.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  {name:26s} {len(rows):5d} rows -> {path}")
    return len(rows)


# --------------------------------------------------------------------------- #
def gen_hcps(n=300):
    rows = []
    for i in range(1, n + 1):
        inst, city, st, region = random.choice(INSTITUTIONS)
        territory = random.choice(TERRITORY_BY_REGION[region])
        tier = random.choices(TIERS, weights=[0.2, 0.4, 0.4])[0]
        specialty = random.choice(SPECIALTIES)
        pubs = random.randint(0, 90) if tier == "Tier 1 KOL" else random.randint(0, 35)
        trials = random.randint(0, 12) if tier == "Tier 1 KOL" else random.randint(0, 4)
        influence = min(100, int(20 + pubs * 0.6 + trials * 3 + random.randint(0, 25)))
        name = f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        rows.append([
            rid("HCP", i), name, specialty, inst, city, st, territory,
            random.choice(PRACTICE_SETTINGS), tier, pubs, trials, influence,
            f"{random.randint(1000000000, 1999999999)}", "Oncology",
        ])
    header = ["hcp_id", "hcp_name", "specialty", "institution", "city", "state", "territory",
              "practice_setting", "hcp_tier", "publication_count", "trial_participation",
              "influence_score", "npi", "primary_therapeutic_area"]
    return header, rows


def gen_msl_notes(hcp_ids, n=500):
    """Free-text MSL interaction notes — the unstructured GenAI input."""
    rows = []
    for i in range(1, n + 1):
        hcp = random.choice(hcp_ids)
        topic_text, _ = random.choice(TOPIC_LIBRARY)
        product = random.choice(PRODUCT_NAMES)
        indication = random.choice(PRODUCTS[product]["indications"])
        sentiment = random.choice(SENTIMENTS)
        interest = random.choice(INTEREST)
        need = random.choice(INFO_NEEDS)
        competitor = random.choice(COMPETITORS)
        channel = random.choice(CHANNELS)
        evidence = random.choice(EVIDENCE_TYPES)
        follow_up = random.random() < 0.45
        idate = rand_date(TODAY - timedelta(days=270), TODAY)
        duration = random.choice([15, 20, 30, 30, 45, 60])

        comp_clause = ("" if competitor == "None"
                       else f" HCP compared experience with {competitor} and asked how our data differs.")
        fu_clause = (" Requested a follow-up with additional materials."
                     if follow_up else " No specific follow-up requested at this time.")
        note = (
            f"Met with the HCP via {channel.lower()} to discuss {topic_text} for {product} "
            f"({PRODUCTS[product]['inn']}) in {indication}. Overall tone was {sentiment.lower()} and "
            f"scientific interest appeared {interest.lower()}. {need} regarding {evidence.lower()} evidence."
            f"{comp_clause}{fu_clause} Non-promotional scientific exchange only."
        )
        rows.append([rid("INT", i), hcp, random.choice(MSL_NAMES),
                     idate.isoformat(), channel, duration, note])
    header = ["interaction_id", "hcp_id", "msl_name", "interaction_date",
              "channel", "duration_minutes", "raw_notes"]
    return header, rows


def gen_inquiries(hcp_ids, n=400):
    rows = []
    topics = ["Efficacy data request", "Safety / ILD management", "Dosing guidance",
              "Biomarker testing", "Comparative data", "Real-world evidence",
              "Trial enrollment", "CNS efficacy", "Subgroup analysis"]
    for i in range(1, n + 1):
        hcp = random.choice(hcp_ids)
        product = random.choice(PRODUCT_NAMES)
        indication = random.choice(PRODUCTS[product]["indications"])
        idate = rand_date(TODAY - timedelta(days=240), TODAY)
        sla_target = random.choice([2, 3, 5])
        status = random.choices(["Closed", "Open", "In Progress"], weights=[0.62, 0.23, 0.15])[0]
        if status == "Closed":
            resp = random.randint(1, 8)
        elif status == "In Progress":
            resp = (TODAY - idate).days
        else:
            resp = (TODAY - idate).days
        sla_met = status == "Closed" and resp <= sla_target
        rows.append([rid("INQ", i), hcp, idate.isoformat(), random.choice(topics),
                     random.choice(EVIDENCE_TYPES), indication, status, resp,
                     sla_met, sla_target, product])
    header = ["inquiry_id", "hcp_id", "inquiry_date", "inquiry_topic", "evidence_type_requested",
              "indication", "response_status", "response_time_days", "sla_met",
              "sla_target_days", "product"]
    return header, rows


def gen_congress(hcp_ids, n=420):
    rows = []
    for i in range(1, n + 1):
        hcp = random.choice(hcp_ids)
        ev, region, ev_date = random.choice(CONGRESS_EVENTS)
        topic_text, _ = random.choice(TOPIC_LIBRARY)
        status = random.choices(["Attended", "Registered", "No-show"], weights=[0.68, 0.2, 0.12])[0]
        booth = status == "Attended" and random.random() < 0.4
        rows.append([rid("EVT", i), hcp, ev, ev_date.isoformat(),
                     topic_text[:60], "Oncology", status, booth])
    header = ["event_attendance_id", "hcp_id", "event_name", "event_date", "session_topic",
              "therapeutic_area", "attendance_status", "visited_medical_booth"]
    return header, rows


def gen_digital(hcp_ids, n=500):
    rows = []
    titles = [
        "Enhertu DESTINY-Breast04 Efficacy Overview", "Managing ILD: Monitoring & Dose Modification",
        "HER2-low Testing: A Practical Guide", "Datroway TROPION-Lung Data Summary",
        "TROP2 Biomarker Science", "CNS Outcomes with T-DXd", "Real-World Evidence Digest",
        "Sequencing After Antibody-Drug Conjugates", "HER2-ultralow Emerging Data",
    ]
    types = ["Email", "Webinar", "Web Article", "Video", "Interactive Module"]
    for i in range(1, n + 1):
        hcp = random.choice(hcp_ids)
        adate = rand_date(TODAY - timedelta(days=180), TODAY)
        sent = random.randint(1, 6)
        opened = random.randint(0, sent)
        clicks = random.randint(0, opened * 3)
        webinar = random.random() < 0.25
        mins = random.randint(0, 45) if webinar else random.randint(0, 12)
        rows.append([rid("DIG", i), hcp, adate.isoformat(), sent, opened,
                     random.choice(titles), random.choice(types), clicks, webinar, mins])
    header = ["engagement_id", "hcp_id", "activity_date", "emails_sent", "emails_opened",
              "content_title", "content_type", "webpage_clicks", "attended_webinar",
              "content_minutes_viewed"]
    return header, rows


def gen_pubs(hcp_ids, n=350):
    rows = []
    journals = ["NEJM", "Lancet Oncology", "JCO", "Annals of Oncology", "Nature Medicine",
                "JAMA Oncology", "Cancer Discovery"]
    reg = ["ClinicalTrials.gov"]
    titles = [
        "Trastuzumab deruxtecan in HER2-low metastatic breast cancer",
        "Datopotamab deruxtecan in previously treated NSCLC",
        "Intracranial efficacy of T-DXd in brain metastases",
        "Real-world outcomes with antibody-drug conjugates",
        "HER2-ultralow: redefining biomarker thresholds",
        "Management of ADC-related interstitial lung disease",
        "Sequencing strategies after T-DXd progression",
    ]
    for i in range(1, n + 1):
        hcp = random.choice(hcp_ids)
        rtype = random.choices(["Publication", "Clinical Trial"], weights=[0.6, 0.4])[0]
        year = random.choice([2023, 2024, 2024, 2025, 2025, 2026])
        if rtype == "Publication":
            venue = random.choice(journals)
            trial_id = ""
            cites = random.randint(0, 220)
        else:
            venue = random.choice(reg)
            trial_id = f"NCT0{random.randint(4000000, 6999999)}"
            cites = 0
        rows.append([rid("REC", i), hcp, rtype, random.choice(titles), venue, year,
                     "Oncology", trial_id, cites])
    header = ["record_id", "hcp_id", "record_type", "title", "journal_or_registry", "year",
              "therapeutic_area", "trial_id", "citation_count"]
    return header, rows


def gen_claims(n=300):
    rows = []
    diagnoses = [("HER2+ breast cancer", "Enhertu"), ("HER2-low breast cancer", "Enhertu"),
                 ("HER2+ gastric cancer", "Enhertu"), ("HER2-mutant NSCLC", "Enhertu"),
                 ("TROP2 NSCLC", "Datroway"), ("HR+/HER2- breast cancer", "Datroway"),
                 ("FLT3-ITD+ AML", "Vanflyta")]
    i = 0
    for inst, city, st, region in INSTITUTIONS:
        for territory in TERRITORY_BY_REGION[region]:
            for _ in range(random.randint(3, 5)):
                i += 1
                if i > n:
                    break
                diag, therapy = random.choice(diagnoses)
                diagnosed = random.randint(40, 600)
                treated = int(diagnosed * random.uniform(0.15, 0.7))
                pen = round(treated / diagnosed * 100, 2)
                rows.append([rid("CLM", i), city, st, territory, diag, therapy,
                             diagnosed, treated, pen])
    header = ["claim_summary_id", "city", "state", "territory", "diagnosis", "primary_therapy",
              "diagnosed_patient_count", "treated_patient_count", "treatment_penetration_rate"]
    return header, rows[:n]


def gen_approved_content(n=70):
    rows = []
    cats = [c for _, c in TOPIC_LIBRARY]
    cats = sorted(set(cats))
    types = ["Slide Deck", "Publication Reprint", "FAQ Document", "Congress Summary",
             "Clinical Data Summary", "Safety Guide"]
    i = 0
    for cat in cats:
        for _ in range(random.randint(7, 11)):
            i += 1
            if i > n:
                break
            product = random.choice(PRODUCT_NAMES)
            indication = random.choice(PRODUCTS[product]["indications"])
            title = f"{cat}: {product} {indication[:28]}"
            approval = rand_date(date(2025, 1, 1), TODAY)
            status = random.choices(["Approved", "Approved", "Expired"], weights=[0.8, 0.1, 0.1])[0]
            rows.append([rid("CON", i), title[:90], random.choice(types), cat, indication,
                         product, approval.isoformat(), status, f"MED-{random.randint(10000, 99999)}"])
    header = ["content_id", "content_title", "content_type", "topic_category", "indication",
              "product", "approval_date", "approval_status", "med_review_id"]
    return header, rows[:n]


def gen_content_shared(hcp_ids, content_rows, n=320):
    rows = []
    approved = [c for c in content_rows if c[7] == "Approved"]
    for i in range(1, n + 1):
        hcp = random.choice(hcp_ids)
        c = random.choice(approved)
        sdate = rand_date(TODAY - timedelta(days=200), TODAY)
        rows.append([rid("SHR", i), hcp, c[0], c[1], c[2], c[3], sdate.isoformat(),
                     random.choice(MSL_NAMES), random.choice(["In-person", "Email", "Virtual", "Congress"])])
    header = ["share_id", "hcp_id", "content_id", "content_title", "content_type",
              "topic_category", "shared_date", "shared_by_msl", "share_channel"]
    return header, rows


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=".", help="output directory for CSVs")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    print(f"Generating synthetic Daiichi Sankyo Medical Affairs data (seed={SEED}) -> {args.out}")
    total = 0

    h, hcps = gen_hcps(300)
    total += write_csv(args.out, "hcp_master", h, hcps)
    hcp_ids = [r[0] for r in hcps]

    h, r = gen_msl_notes(hcp_ids, 500);          total += write_csv(args.out, "msl_interactions", h, r)
    h, r = gen_inquiries(hcp_ids, 400);          total += write_csv(args.out, "medical_inquiries", h, r)
    h, r = gen_congress(hcp_ids, 420);           total += write_csv(args.out, "congress_events", h, r)
    h, r = gen_digital(hcp_ids, 500);            total += write_csv(args.out, "digital_engagement", h, r)
    h, r = gen_pubs(hcp_ids, 350);               total += write_csv(args.out, "publications_trials", h, r)
    h, r = gen_claims(300);                      total += write_csv(args.out, "patient_claims_summary", h, r)
    h, content = gen_approved_content(70);       total += write_csv(args.out, "approved_content", h, content)
    h, r = gen_content_shared(hcp_ids, content, 320); total += write_csv(args.out, "content_shared", h, r)

    print(f"Done. {total} total synthetic rows across 9 datasets.")


if __name__ == "__main__":
    main()
