import sys, os
sys.path.insert(0, '.')
from backend.app.database import SessionLocal
from backend.app.models.observation import Observation
from backend.app.models.species import Species

db = SessionLocal()
unmatched = db.query(Observation).filter(Observation.species_id.is_(None)).count()
print(f"Unmatched in DB: {unmatched}")
