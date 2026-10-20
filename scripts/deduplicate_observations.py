import sys, os
import json
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(".")))

from backend.app.database import SessionLocal
from backend.app.models.observation import Observation, DataSource
from backend.app.models.species import Species

db = SessionLocal()

print("==================================================")
print("PHASE 1 — READ-ONLY DIAGNOSIS")
print("==================================================")

all_obs = db.query(Observation, Species.scientific_name, DataSource.name).outerjoin(Species, Observation.species_id == Species.id).join(DataSource, Observation.source_id == DataSource.id).all()

gbif_groups = defaultdict(list)
inat_groups = defaultdict(list)
ebird_groups = defaultdict(list)

# Identify source IDs
for obs, sci_name, source_name in all_obs:
    if not obs.raw_metadata:
        continue
        
    if source_name == "GBIF":
        gbif_key = obs.raw_metadata.get("gbif_key")
        if gbif_key:
            gbif_groups[gbif_key].append((obs, sci_name))
            
    elif source_name == "iNaturalist":
        inat_id = obs.raw_metadata.get("inat_id")
        if inat_id:
            inat_groups[inat_id].append((obs, sci_name))
            
    elif source_name == "eBird":
        ebird_id = obs.raw_metadata.get("ebird_id")
        if ebird_id:
            ebird_groups[ebird_id].append((obs, sci_name))

# Filter to only duplicates
gbif_dupes = {k: v for k, v in gbif_groups.items() if len(v) > 1}
inat_dupes = {k: v for k, v in inat_groups.items() if len(v) > 1}
ebird_dupes = {k: v for k, v in ebird_groups.items() if len(v) > 1}

def print_group(source, key, records):
    print(f"\nGroup: {source} - {key}")
    first_obs, _ = records[0]
    is_exact = True
    for obs, sci_name in records:
        print(f"  ID: {obs.id} | Species: {obs.species_id} ({sci_name}) | Lat: {obs.latitude} | Lon: {obs.longitude} | Date: {obs.observed_at} | Created: {obs.created_at}")
        if (obs.species_id != first_obs.species_id or 
            obs.latitude != first_obs.latitude or 
            obs.longitude != first_obs.longitude or 
            obs.observed_at != first_obs.observed_at):
            is_exact = False
    
    print(f"  -> Diagnosis: {'EXACT DUPLICATE RECORDS' if is_exact else 'RECORDS THAT DIFFER IN IMPORTANT FIELDS'}")
    return is_exact

gbif_exact = 0
inat_exact = 0
ebird_exact = 0

for k, v in gbif_dupes.items():
    if print_group("GBIF", k, v): gbif_exact += 1
for k, v in inat_dupes.items():
    if print_group("iNaturalist", k, v): inat_exact += 1
for k, v in ebird_dupes.items():
    if print_group("eBird", k, v): ebird_exact += 1

print("\n==================================================")
print("PHASES 2-6 — SAFE REMOVAL")
print("==================================================")

to_delete_ids = []
gbif_removed = 0
inat_removed = 0
ebird_removed = 0

def process_deletions(dupes, source_type):
    global gbif_removed, inat_removed, ebird_removed
    for k, v in dupes.items():
        # Check if they are exact duplicates by our definition
        # Same source, source_record_id, species_id
        # We enforce species_id must match to be considered exact duplicate
        first_obs, _ = v[0]
        all_same_species = all(obs.species_id == first_obs.species_id for obs, _ in v)
        if not all_same_species:
            print(f"Skipping {source_type} {k} - species IDs differ")
            continue
            
        # Sort by earliest created_at (tiebreaker)
        sorted_obs = sorted(v, key=lambda x: (x[0].created_at or '9999', x[0].id))
        
        canonical = sorted_obs[0][0]
        duplicates = [x[0] for x in sorted_obs[1:]]
        
        for d in duplicates:
            print(f"Queueing deletion for {source_type} Observation ID {d.id} (Canonical: {canonical.id})")
            to_delete_ids.append(d.id)
            if source_type == "GBIF": gbif_removed += 1
            elif source_type == "iNaturalist": inat_removed += 1
            elif source_type == "eBird": ebird_removed += 1

process_deletions(gbif_dupes, "GBIF")
process_deletions(inat_dupes, "iNaturalist")
process_deletions(ebird_dupes, "eBird")

if to_delete_ids:
    print(f"Executing deletion of {len(to_delete_ids)} records in transaction...")
    try:
        db.query(Observation).filter(Observation.id.in_(to_delete_ids)).delete(synchronize_session=False)
        db.commit()
        print("Deletion successful.")
    except Exception as e:
        db.rollback()
        print(f"Error during deletion: {e}")
else:
    print("No records to delete.")


print("\n==================================================")
print("PHASE 8 & 9 — FINAL REPORT DATA")
print("==================================================")

total_species = db.query(Species).count()
total_obs = db.query(Observation).count()

# Re-check dupes
new_all_obs = db.query(Observation, DataSource.name).join(DataSource, Observation.source_id == DataSource.id).all()
new_gbif = defaultdict(list)
new_inat = defaultdict(list)
new_ebird = defaultdict(list)
for obs, source_name in new_all_obs:
    if not obs.raw_metadata: continue
    if source_name == "GBIF":
        if obs.raw_metadata.get("gbif_key"): new_gbif[obs.raw_metadata.get("gbif_key")].append(obs)
    elif source_name == "iNaturalist":
        if obs.raw_metadata.get("inat_id"): new_inat[obs.raw_metadata.get("inat_id")].append(obs)
    elif source_name == "eBird":
        if obs.raw_metadata.get("ebird_id"): new_ebird[obs.raw_metadata.get("ebird_id")].append(obs)

post_gbif_dupes = len([k for k, v in new_gbif.items() if len(v) > 1])
post_inat_dupes = len([k for k, v in new_inat.items() if len(v) > 1])
post_ebird_dupes = len([k for k, v in new_ebird.items() if len(v) > 1])

null_species = db.query(Observation).filter(Observation.species_id == None).count()
broken_refs = db.query(Observation).outerjoin(Species, Observation.species_id == Species.id).filter(Species.id == None).count()

print(f"Species: {total_species}")
print(f"Observations: {total_obs}")
print(f"Duplicate GBIF source IDs: {post_gbif_dupes}")
print(f"Duplicate iNaturalist source IDs: {post_inat_dupes}")
print(f"Duplicate eBird source IDs: {post_ebird_dupes}")
print(f"NULL species_id: {null_species}")
print(f"Broken species references: {broken_refs}")
print(f"GBIF Groups: {len(gbif_dupes)}, Removed: {gbif_removed}")
print(f"iNat Groups: {len(inat_dupes)}, Removed: {inat_removed}")
print(f"eBird Groups: {len(ebird_dupes)}, Removed: {ebird_removed}")

db.close()
