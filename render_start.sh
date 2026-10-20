# Start script for Render Web Service (FastAPI)
set -e

# In native Render Python environments where buildCommand ran, dependencies are already installed.
# Only run fallback install if requirements or spacy are missing:
if ! python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null; then
  echo "Downloading spaCy en_core_web_sm model..."
  python -m spacy download en_core_web_sm || true
fi

echo "=== [3/4] Initializing Database & Seed Reference Data ==="
python -c "
import os, sys
sys.path.insert(0, '.')
from backend.app.database import init_db
from backend.app.services.gamification_service import seed_roles, seed_badges
from backend.app.database import SessionLocal

print('Initializing schema and extensions (PostGIS/pgvector)...')
init_db()
print('Seeding default RBAC roles and badges...')
with SessionLocal() as db:
    seed_roles(db)
    seed_badges(db)
print('Database initialization complete.')
"

echo "=== [4/4] Starting Uvicorn Server ==="
exec uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
