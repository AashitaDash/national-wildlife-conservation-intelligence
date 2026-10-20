import sys
import os

# Add root to pythonpath
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from backend.app.database import engine

def migrate():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE species ADD COLUMN image_source VARCHAR(50);"))
            print("Added image_source")
        except Exception as e:
            print(f"Error: {e}")
        try:
            conn.execute(text("ALTER TABLE species ADD COLUMN image_license VARCHAR(100);"))
            print("Added image_license")
        except Exception as e:
            print(f"Error: {e}")
        try:
            conn.execute(text("ALTER TABLE species ADD COLUMN image_attribution VARCHAR(500);"))
            print("Added image_attribution")
        except Exception as e:
            print(f"Error: {e}")
            
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
