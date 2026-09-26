"""Grant the Databricks App service principal access to the Lakebase tables.

Runs on Databricks serverless. Finds the app SP's PostgreSQL role and grants
read on the synced action queue and read/write on the review write-back table.
"""
import ssl
import uuid
import pg8000.dbapi
from databricks.sdk import WorkspaceClient

INSTANCE = "moa-medical-copilot"
DB = "databricks_postgres"
SP_CLIENT_ID = "6b2f5b3e-b5e5-4573-9199-7164bff0b8f2"
SP_NAME = "moa-medical-copilot"

w = WorkspaceClient()
inst = w.database.get_database_instance(name=INSTANCE)
cred = w.database.generate_database_credential(
    request_id=str(uuid.uuid4()), instance_names=[INSTANCE])
user = w.current_user.me().user_name

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
conn = pg8000.dbapi.connect(user=user, password=cred.token, host=inst.read_write_dns,
                            port=5432, database=DB, ssl_context=ctx)
conn.autocommit = True
cur = conn.cursor()

cur.execute("SELECT rolname FROM pg_roles WHERE rolname LIKE %s OR rolname LIKE %s",
            ('%' + SP_CLIENT_ID + '%', '%' + SP_NAME + '%'))
roles = [r[0] for r in cur.fetchall()]
print("candidate SP roles:", roles)

for role in roles:
    cur.execute(f'GRANT USAGE ON SCHEMA public TO "{role}"')
    cur.execute(f'GRANT SELECT ON public.msl_action_queue TO "{role}"')
    cur.execute(f'GRANT SELECT, INSERT ON public.msl_review_actions TO "{role}"')
    cur.execute(f'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "{role}"')
    print("granted read/write to", role)

if not roles:
    print("No SP role found yet (created lazily on first connect). "
          "Re-run after the app first connects, or the app user grant is inherited.")
conn.close()
print("DONE")
