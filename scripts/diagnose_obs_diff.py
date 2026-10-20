import sys, os
from sqlalchemy import func
sys.path.insert(0, os.path.dirname(os.path.abspath(".")))

from backend.app.database import SessionLocal
from backend.app.models.observation import Observation, DataSource
from backend.app.models.species import Species

db = SessionLocal()

print("--- AUDIT START ---")
total_obs = db.query(Observation).count()
total_species = db.query(Species).count()

print(f"Total Observations: {total_obs}")
print(f"Total Species: {total_species}")

print("\n--- Observation Counts by Source ---")
source_counts = db.query(DataSource.name, func.count(Observation.id)).join(Observation, DataSource.id == Observation.source_id).group_by(DataSource.name).all()
for src_name, count in source_counts:
    print(f"  {src_name}: {count}")

print("\n--- Unmapped Source Counts ---")
unmapped = db.query(func.count(Observation.id)).filter(Observation.source_id == None).scalar()
if unmapped:
    print(f"  No Source ID (NULL): {unmapped}")

print("\n--- Recent Ingestion Timestamps ---")
from collections import defaultdict
min_counts = defaultdict(int)
all_obs = db.query(Observation.created_at, Observation.raw_metadata, Observation.source_id).all()
for created_at, raw_metadata, source_id in all_obs:
    if created_at:
        min_counts[created_at.strftime('%Y-%m-%d %H:%M')] += 1

for dt in sorted(min_counts.keys()):
    if min_counts[dt] > 0:
        print(f"  {dt}: {min_counts[dt]}")

print("\n--- Duplicate Source IDs ---")
gbif_keys = set()
inat_ids = set()
gbif_dupes = 0
inat_dupes = 0
for _, raw_metadata, _ in all_obs:
    if not raw_metadata: continue
    
    gbif_key = raw_metadata.get('gbif_key')
    if gbif_key:
        if gbif_key in gbif_keys:
            gbif_dupes += 1
        gbif_keys.add(gbif_key)
        
    inat_id = raw_metadata.get('inat_id')
    if inat_id:
        if inat_id in inat_ids:
            inat_dupes += 1
        inat_ids.add(inat_id)

print(f"Duplicate GBIF Source IDs: {gbif_dupes}")
print(f"Duplicate iNat Source IDs: {inat_dupes}")

print("\n--- Integrity Checks ---")
null_species = db.query(Observation).filter(Observation.species_id == None).count()
print(f"NULL species_id: {null_species}")

broken_refs = db.query(Observation).outerjoin(Species, Observation.species_id == Species.id).filter(Species.id == None).count()
print(f"Broken species references: {broken_refs}")

print("\n--- Deduplication Check ---")
dupes = db.query(
    Observation.species_id, Observation.latitude, Observation.longitude, Observation.observed_at, func.count(Observation.id)
).group_by(
    Observation.species_id, Observation.latitude, Observation.longitude, Observation.observed_at
).having(func.count(Observation.id) > 1).count()
print(f"Possible duplicate records (exact match on species, lat, lon, date): {dupes}")

print("--- AUDIT END ---")
db.close()
