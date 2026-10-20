import sys
import json
sys.path.insert(0, '.')
from sqlalchemy import func
from backend.app.database import SessionLocal
from backend.app.models.species import Species
from backend.app.models.observation import Observation, DataSource

db = SessionLocal()

gbif_src = db.query(DataSource).filter(DataSource.name == 'GBIF').first()
inat_src = db.query(DataSource).filter(DataSource.name == 'iNaturalist').first()

if gbif_src:
    gbif_obs = db.query(Observation).filter(Observation.source_id == gbif_src.id).all()
    print("GBIF:")
    print(f"- total observations: {len(gbif_obs)}")
    
    # Check distinct scientific names from associated Species
    sp_ids = set(o.species_id for o in gbif_obs)
    sp_names = [db.query(Species).get(s).scientific_name for s in sp_ids]
    print(f"- distinct scientific names (in DB): {len(set(sp_names))} {sp_names}")
    
    # Check distinct source/taxon IDs in raw_metadata
    gbif_keys = set(o.raw_metadata.get("gbif_key") for o in gbif_obs if isinstance(o.raw_metadata, dict) and o.raw_metadata.get("gbif_key"))
    print(f"- distinct taxon/source IDs (gbif_key): {len(gbif_keys)}")
    
if inat_src:
    inat_obs = db.query(Observation).filter(Observation.source_id == inat_src.id).all()
    print("iNaturalist:")
    print(f"- total observations: {len(inat_obs)}")
    
    sp_ids = set(o.species_id for o in inat_obs)
    sp_names = [db.query(Species).get(s).scientific_name for s in sp_ids]
    print(f"- distinct scientific names (in DB): {len(set(sp_names))} {sp_names}")
    
    inat_ids = set(o.raw_metadata.get("inat_id") for o in inat_obs if isinstance(o.raw_metadata, dict) and o.raw_metadata.get("inat_id"))
    print(f"- distinct taxon IDs (inat_id): {len(inat_ids)}")

print("Deduplication:")
collisions = db.query(
    Observation.source_id, Observation.latitude, Observation.longitude, Observation.observed_at, func.count(Observation.id)
).group_by(
    Observation.source_id, Observation.latitude, Observation.longitude, Observation.observed_at
).having(func.count(Observation.id) > 1).all()

print(f"- 70 fingerprint collisions? Found {len(collisions)}")

unique_source_ids = 0
identical_source_ids = 0
legitimate_observations = 0

for c in collisions:
    obs_list = db.query(Observation).filter(
        Observation.source_id == c[0],
        Observation.latitude == c[1],
        Observation.longitude == c[2],
        Observation.observed_at == c[3]
    ).all()
    
    src_ids = []
    for o in obs_list:
        meta = o.raw_metadata or {}
        if o.source_id == gbif_src.id:
            src_ids.append(meta.get("gbif_key"))
        elif o.source_id == inat_src.id:
            src_ids.append(meta.get("inat_id"))
        else:
            # eBird or other
            src_ids.append(meta.get("subId", meta.get("obsId", str(o.id))))
            
    # filter out Nones
    src_ids = [s for s in src_ids if s is not None]
    
    if len(set(src_ids)) == len(obs_list):
        unique_source_ids += 1
        legitimate_observations += len(obs_list)
    else:
        identical_source_ids += 1

print(f"- unique source IDs (groups): {unique_source_ids}")
print(f"- identical source IDs (groups with at least some identical keys): {identical_source_ids}")
print(f"- likely legitimate observations inside these collisions: {legitimate_observations}")
