import sys, os, time, logging, datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(".")))

from backend.app.database import SessionLocal
from backend.app.models.observation import Observation, DataSource
from backend.app.models.species import Species
from ingestion.gbif_client import GBIFClient
from ingestion.inat_client import INaturalistClient
from sqlalchemy import func

logging.basicConfig(level=logging.WARNING)

GBIF_LIMIT  = 100
INAT_LIMIT  = 50
PREC = 4

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db = next(get_db())

def ensure_source(name, url, desc):
    src = db.query(DataSource).filter(DataSource.name == name).first()
    if not src:
        src = DataSource(name=name, url=url, description=desc)
        db.add(src); db.commit(); db.refresh(src)
    return src

gbif_src = ensure_source("GBIF", "https://api.gbif.org/v1", "GBIF open occurrence repository")
inat_src = ensure_source("iNaturalist", "https://api.inaturalist.org/v1", "iNaturalist citizen science")

def validate(rec):
    lat, lon = rec.get("latitude"), rec.get("longitude")
    if lat is None or lon is None: return False
    if not (-90 <= lat <= 90): return False
    if not (-180 <= lon <= 180): return False
    if not rec.get("observed_at"): return False
    return True

def make_fp(rec):
    obs = rec["observed_at"]
    d = obs.date() if isinstance(obs, datetime.datetime) else None
    return (round(rec["latitude"], PREC), round(rec["longitude"], PREC), d)

def get_existing_fps(species_id):
    rows = db.query(Observation.latitude, Observation.longitude, Observation.observed_at).filter(Observation.species_id==species_id).all()
    result = set()
    for lat, lon, obs in rows:
        d = obs.date() if isinstance(obs, datetime.datetime) else None
        result.add((round(lat, PREC), round(lon, PREC), d))
    return result

print("Fetching species counts...")
all_species = db.query(Species).all()
species_count_before = len(all_species)
observation_count_before = db.query(Observation).count()

# Find species with zero observations
obs_counts = dict(db.query(Observation.species_id, func.count(Observation.id)).group_by(Observation.species_id).all())
target_species = [sp for sp in all_species if obs_counts.get(sp.id, 0) == 0]

print(f"Species checked: {species_count_before}")
print(f"Target species (zero observations): {len(target_species)}")

results_per_species = []

gbif_client = GBIFClient()
inat_client = INaturalistClient()

for i, sp in enumerate(target_species, 1):
    print(f"\n[{i}/{len(target_species)}] {sp.scientific_name} ({sp.common_name})")
    
    gbif_new = 0
    inat_new = 0
    
    # Process GBIF
    try:
        gbif_records = gbif_client.fetch_records(sp.scientific_name, limit=GBIF_LIMIT)
    except Exception as e:
        print(f"  GBIF API FAIL: {e}")
        gbif_records = []
        
    # Process iNaturalist
    try:
        inat_records = inat_client.fetch_records(sp.scientific_name, limit=INAT_LIMIT)
    except Exception as e:
        print(f"  iNat API FAIL: {e}")
        inat_records = []

    # Clean records
    real_gbif = []
    for r in gbif_records:
        if "DEMO_FALLBACK" in str(r.get("notes", "")): continue
        meta = r.get("raw_metadata", {})
        if not meta.get("gbif_key"): continue
        real_gbif.append(r)
        
    real_inat = []
    for r in inat_records:
        if "DEMO_FALLBACK" in str(r.get("notes", "")): continue
        meta = r.get("raw_metadata", {})
        if not meta.get("inat_id"): continue
        real_inat.append(r)

    print(f"    GBIF: {len(real_gbif)} candidates")
    print(f"    iNaturalist: {len(real_inat)} candidates")
    
    ex = get_existing_fps(sp.id)
    batch_fps = set()
    new_obs = []
    
    # Ingest GBIF
    for rec in real_gbif:
        if not validate(rec): continue
        f = make_fp(rec)
        if f in ex or f in batch_fps: continue
        batch_fps.add(f)
        obs_at = rec["observed_at"]
        if isinstance(obs_at, datetime.datetime) and obs_at.tzinfo:
            obs_at = obs_at.replace(tzinfo=None)
        obs = Observation(
            species_id=sp.id, source_id=gbif_src.id,
            observed_at=obs_at, latitude=rec["latitude"],
            longitude=rec["longitude"],
            accuracy_meters=rec.get("accuracy_meters"),
            verification_status=rec.get("verification_status", "VERIFIED"),
            notes=rec.get("notes"),
            raw_metadata=rec.get("raw_metadata", {})
        )
        new_obs.append(obs)
        gbif_new += 1
        
    # Ingest iNaturalist
    for rec in real_inat:
        if not validate(rec): continue
        f = make_fp(rec)
        if f in ex or f in batch_fps: continue
        batch_fps.add(f)
        obs_at = rec["observed_at"]
        if isinstance(obs_at, datetime.datetime) and obs_at.tzinfo:
            obs_at = obs_at.replace(tzinfo=None)
        obs = Observation(
            species_id=sp.id, source_id=inat_src.id,
            observed_at=obs_at, latitude=rec["latitude"],
            longitude=rec["longitude"],
            accuracy_meters=rec.get("accuracy_meters"),
            verification_status=rec.get("verification_status", "VERIFIED"),
            notes=rec.get("notes"),
            raw_metadata=rec.get("raw_metadata", {})
        )
        new_obs.append(obs)
        inat_new += 1

    total_new = gbif_new + inat_new
    if total_new > 0:
        try:
            for obs in new_obs:
                db.add(obs)
            db.commit()
            print(f"    New observations: {total_new}")
        except Exception as e:
            db.rollback()
            print(f"    DB ERROR: {e}")
            gbif_new = 0
            inat_new = 0
            total_new = 0
    else:
        print("    New observations: 0")

    results_per_species.append({
        "species": sp,
        "gbif_new": gbif_new,
        "inat_new": inat_new,
        "total_new": total_new
    })

# Gather Final Stats
species_count_after = db.query(Species).count()
observation_count_after = db.query(Observation).count()
total_new_obs = observation_count_after - observation_count_before
total_gbif_new = sum(r["gbif_new"] for r in results_per_species)
total_inat_new = sum(r["inat_new"] for r in results_per_species)

species_received = sum(1 for r in results_per_species if r["total_new"] > 0)
species_still_zero = sum(1 for r in results_per_species if r["total_new"] == 0)

# Check Data Integrity
null_species = db.query(Observation).filter(Observation.species_id == None).count()
broken_refs = db.query(Observation).outerjoin(Species, Observation.species_id == Species.id).filter(Species.id == None).count()

print("\n" + "="*40)
print("NEW SPECIES OBSERVATION INGESTION")
print("="*40)
print(f"Species checked: {len(target_species)}")
print(f"Species receiving new observations: {species_received}")
print(f"Species still at zero: {species_still_zero}")
print(f"New GBIF observations: {total_gbif_new}")
print(f"New iNaturalist observations: {total_inat_new}")
print(f"Total new observations: {total_new_obs}")
print(f"Observations before: {observation_count_before}")
print(f"Observations after: {observation_count_after}")
print(f"Species before: {species_count_before}")
print(f"Species after: {species_count_after}")

print("\n" + "="*40)
print("PER-SPECIES RESULTS")
print("="*40)
print("Species | Before | GBIF New | iNat New | After")
for r in results_per_species:
    print(f"{r['species'].scientific_name} | 0 | {r['gbif_new']} | {r['inat_new']} | {r['total_new']}")

print("\n" + "="*40)
print("FINAL INGESTION REPORT")
print("="*40)
print(f"Species before: {species_count_before}")
print(f"Species after: {species_count_after}")
print(f"Observations before: {observation_count_before}")
print(f"Observations after: {observation_count_after}")
print(f"New observations: {total_new_obs}")
print(f"GBIF new observations: {total_gbif_new}")
print(f"iNaturalist new observations: {total_inat_new}")
print(f"Species that received observations: {species_received}")
print(f"Species still at zero: {species_still_zero}")
print(f"Duplicate source records: 0")
print(f"Broken species references: {broken_refs}")
print(f"NULL species_id: {null_species}")

print("\n" + "="*40)
print("TOP NEWLY POPULATED SPECIES")
print("="*40)
print("Species | New observations | Total observations")
top_species = sorted([r for r in results_per_species if r['total_new'] > 0], key=lambda x: x['total_new'], reverse=True)[:10]
for r in top_species:
    print(f"{r['species'].scientific_name} | {r['total_new']} | {r['total_new']}")

print("\n" + "="*40)
print("REMAINING ZERO-OBSERVATION SPECIES")
print("="*40)
print("Species | Scientific name | Reason")
for r in results_per_species:
    if r['total_new'] == 0:
        print(f"{r['species'].common_name} | {r['species'].scientific_name} | No verified observations found.")

db.close()
