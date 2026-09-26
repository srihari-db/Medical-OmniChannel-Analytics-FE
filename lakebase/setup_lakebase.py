"""Lakebase operational-serving setup for the Medical Engagement Copilot.

Runs on Databricks compute (same network as the Lakebase instance). Creates the
MSL write-back table, verifies the reverse-ETL synced action queue, and seeds a
couple of demo review actions so the operational loop is demonstrably working.

Uses pg8000 (pure-Python PostgreSQL driver) for portability across Databricks
serverless runtimes. The Databricks App uses psycopg at runtime (see app/).

Instance : moa-medical-copilot  (Lakebase Provisioned, PG 16)
Database : databricks_postgres   (UC catalog: moa_lakebase)
Tables   : public.msl_action_queue     (synced from _sa701.moa.serving_msl_action_queue)
           public.msl_review_actions   (operational write-back — MSL decisions)
"""
import ssl
import uuid
import pg8000.dbapi
from databricks.sdk import WorkspaceClient

INSTANCE = "moa-medical-copilot"
DBNAME = "databricks_postgres"

w = WorkspaceClient()
inst = w.database.get_database_instance(name=INSTANCE)
cred = w.database.generate_database_credential(
    request_id=str(uuid.uuid4()), instance_names=[INSTANCE])
user = w.current_user.me().user_name

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

conn = pg8000.dbapi.connect(
    user=user, password=cred.token, host=inst.read_write_dns, port=5432,
    database=DBNAME, ssl_context=ctx)
conn.autocommit = True
cur = conn.cursor()

# --- operational write-back table (MSL review decisions) -------------------
cur.execute("""
CREATE TABLE IF NOT EXISTS public.msl_review_actions (
    action_id        BIGSERIAL PRIMARY KEY,
    hcp_id           TEXT NOT NULL,
    msl_name         TEXT,
    review_decision  TEXT,
    review_notes     TEXT,
    scheduled_channel TEXT,
    scheduled_date   DATE,
    reviewed_at      TIMESTAMPTZ DEFAULT now()
);""")
cur.execute("CREATE INDEX IF NOT EXISTS idx_review_hcp ON public.msl_review_actions(hcp_id);")

# --- verify the synced action queue landed ---------------------------------
cur.execute("SELECT count(*) FROM public.msl_action_queue;")
print("[synced] public.msl_action_queue rows =", cur.fetchone()[0])

cur.execute("""SELECT hcp_id, hcp_name, priority_tier, round(msl_priority_score::numeric,1), trigger
               FROM public.msl_action_queue ORDER BY msl_priority_score DESC LIMIT 5;""")
print("[synced] top-5 MSL priorities:")
for r in cur.fetchall():
    print("   ", r)

# --- seed two demo write-back actions (idempotent) -------------------------
cur.execute("SELECT count(*) FROM public.msl_review_actions;")
if cur.fetchone()[0] == 0:
    cur.execute("SELECT hcp_id FROM public.msl_action_queue ORDER BY msl_priority_score DESC LIMIT 2;")
    top = [r[0] for r in cur.fetchall()]
    for hid in top:
        cur.execute("""INSERT INTO public.msl_review_actions
            (hcp_id, msl_name, review_decision, review_notes, scheduled_channel, scheduled_date)
            VALUES (%s, %s, %s, %s, %s, current_date + 14);""",
            (hid, "Dr. Amara Osei", "Approved",
             "Confirmed next-best-engagement; will share approved evidence.", "In-person"))
    print("[write-back] seeded", len(top), "demo review actions")

cur.execute("SELECT count(*) FROM public.msl_review_actions;")
print("[write-back] public.msl_review_actions rows =", cur.fetchone()[0])
cur.execute("SELECT current_user, current_database();")
print("[conn] connected as", cur.fetchone())
conn.close()
print("DONE: Lakebase operational serving ready.")
