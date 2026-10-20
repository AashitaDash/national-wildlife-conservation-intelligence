import sys, os, time, logging, datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(".")))

from backend.app.database import SessionLocal
from backend.app.models.observation import Observation, DataSource
from backend.app.models.species import Species
from ingestion.gbif_client import GBIFClient
from ingestion.inat_client import INaturalistClient

logging.basicConfig(level=logging.WARNING)

GBIF_LIMIT  = 100
INAT_LIMIT  = 50
PREC = 4

db = SessionLocal()

def ensure_source(name, url, desc):
    src = db.query(DataSource).filter(DataSource.name == name).first()
    if not src:
        src = DataSource(name=name, url=url, description=desc)
        db.add(src); db.commit(); db.refresh(src)
    return src

gbif_src = ensure_source("GBIF", "https://api.gbif.org/v1", "GBIF open occurrence repository")
inat_src = ensure_source("iNaturalist", "https://api.inaturalist.org/v1", "iNaturalist citizen science")

species_list = db.query(Species).all()
print(f"Species in DB: {len(species_list)}")
for sp in species_list:
    print(f"  {sp.common_name} ({sp.scientific_name}) [{sp.iucn_category}]")

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

results = {}

def ingest(client, source_db, is_gbif, label):
    print(f"\n[{label}] Starting live ingestion...")
    fetched = valid = duped = persisted = api_fail = 0
    species_hit = []
    for sp in species_list:
        try:
            records = client.fetch_records(sp.scientific_name, limit=GBIF_LIMIT if is_gbif else INAT_LIMIT)
        except Exception as e:
            print(f"  API FAIL {sp.scientific_name}: {e}")
            api_fail += 1
            continue

        real = []
        for r in records:
            if "DEMO_FALLBACK" in str(r.get("notes", "")):
                continue
            meta = r.get("raw_metadata", {})
            if is_gbif and not meta.get("gbif_key"):
                continue
            if not is_gbif and not meta.get("inat_id"):
                continue
            real.append(r)

        fetched += len(real)
        if not real:
            print(f"  {sp.common_name}: 0 real API records")
            continue

        ex = get_existing_fps(sp.id)
        batch_fps = set()
        new_obs = []
        for rec in real:
            if not validate(rec): continue
            valid += 1
            f = make_fp(rec)
            if f in ex or f in batch_fps:
                duped += 1; continue
            batch_fps.add(f); ex.add(f)
            obs_at = rec["observed_at"]
            if isinstance(obs_at, datetime.datetime) and obs_at.tzinfo:
                obs_at = obs_at.replace(tzinfo=None)
            obs = Observation(
                species_id=sp.id, source_id=source_db.id,
                observed_at=obs_at, latitude=rec["latitude"],
                longitude=rec["longitude"],
                accuracy_meters=rec.get("accuracy_meters"),
                verification_status=rec.get("verification_status", "VERIFIED"),
                notes=rec.get("notes"),
                raw_metadata=rec.get("raw_metadata", {})
            )
            new_obs.append(obs)

        if new_obs:
            try:
                for o in new_obs: db.add(o)
                db.commit()
                persisted += len(new_obs)
                species_hit.append(sp.scientific_name)
                print(f"  {sp.common_name}: {len(new_obs)} new records persisted")
            except Exception as e:
                db.rollback()
                print(f"  DB ERROR {sp.scientific_name}: {e}")
        else:
            print(f"  {sp.common_name}: 0 new (all duped or invalid)")

    results[label] = dict(fetched=fetched, valid=valid, duped=duped, persisted=persisted, api_fail=api_fail, species_hit=species_hit)

ingest(GBIFClient(), gbif_src, True, "GBIF")
ingest(INaturalistClient(), inat_src, False, "iNaturalist")

total      = db.query(Observation).count()
gbif_total = db.query(Observation).filter(Observation.source_id==gbif_src.id).count()
inat_total = db.query(Observation).filter(Observation.source_id==inat_src.id).count()
verified   = db.query(Observation).filter(Observation.verification_status=="VERIFIED").count()
citizen    = db.query(Observation).filter(Observation.verification_status=="CITIZEN_PENDING").count()
sp_with    = db.query(Species).join(Observation).distinct().count()

print("\n" + "="*70)
print("INGESTION COMPLETE - FINAL REPORT")
print("="*70)
for label in ["GBIF", "iNaturalist"]:
    r = results.get(label, {})
    print(f"\n  [{label}]")
    print(f"    Fetched (real API only): {r.get('fetched',0)}")
    print(f"    Validated:               {r.get('valid',0)}")
    print(f"    Deduplicated (skipped):  {r.get('duped',0)}")
    print(f"    Persisted:               {r.get('persisted',0)}")
    print(f"    API call failures:       {r.get('api_fail',0)}")
    hits = r.get("species_hit", [])
    if hits:
        print(f"    Species with real data:  {len(hits)}")
        for s in hits:
            print(f"      - {s}")
    else:
        print("    Species with real data:  0")

print(f"\n  [Database Verification]")
print(f"    Total observations:          {total}")
print(f"    From GBIF:                   {gbif_total}")
print(f"    From iNaturalist:            {inat_total}")
print(f"    Verified (authoritative):    {verified}")
print(f"    Citizen pending:             {citizen}")
print(f"    Species with observations:   {sp_with}")
print(f"\n  Records visible via GET /api/v1/observations")
print(f"\n  [Pending - Awaiting API keys]")
print(f"    IUCN Red List: https://api.iucnredlist.org/")
print(f"    eBird:         https://ebird.org/api/keygen")
print("="*70)
db.close()
