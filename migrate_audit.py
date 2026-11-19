import sys
sys.path.insert(0, '.')
from backend.app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'audit_events'"))
    cols = [r[0] for r in res.fetchall()]
    print("Existing audit_events columns:", cols)

    if 'event_metadata' not in cols:
        print("Adding event_metadata to audit_events...")
        conn.execute(text("ALTER TABLE audit_events ADD COLUMN event_metadata JSON;"))
        conn.commit()
    print("audit_events checked!")

