import sys
sys.path.insert(0, '.')
from backend.app.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        print("Checking users table...")
        res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"))
        cols = [r[0] for r in res.fetchall()]
        print("Existing columns:", cols)

        if 'is_suspended' not in cols:
            print("Adding is_suspended...")
            conn.execute(text("ALTER TABLE users ADD COLUMN is_suspended BOOLEAN DEFAULT FALSE;"))
            conn.commit()

        if 'last_active_at' not in cols:
            print("Adding last_active_at...")
            conn.execute(text("ALTER TABLE users ADD COLUMN last_active_at TIMESTAMP WITH TIME ZONE;"))
            conn.commit()

        print("Migration complete!")

if __name__ == "__main__":
    migrate()

