import sys
sys.path.insert(0, '.')
from backend.app.database import SessionLocal
from backend.app.models.observation import Observation
db = SessionLocal()
gbif = db.query(Observation.raw_metadata).filter(Observation.source_id == 1).all()
inat = db.query(Observation.raw_metadata).filter(Observation.source_id == 2).all()
gbif_names = set(r[0].get('scientificName', r[0].get('species')) for r in gbif if r[0])
inat_names = set(r[0].get('taxon', {}).get('name') for r in inat if r[0] and 'taxon' in r[0])
print("GBIF names in metadata:", gbif_names)
print("iNat names in metadata:", inat_names)
