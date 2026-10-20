import sys
sys.path.insert(0, '.')
from sqlalchemy import func, distinct
from backend.app.database import SessionLocal
from backend.app.models.species import Species
from backend.app.models.observation import Observation, DataSource

db = SessionLocal()

print("1. COUNT(*) of species:", db.query(Species).count())
print("2. COUNT(*) of observations:", db.query(Observation).count())
print("3. COUNT(DISTINCT species_id) from observations:", db.query(func.count(distinct(Observation.species_id))).scalar())
print("4. Observations with NULL species_id:", db.query(Observation).filter(Observation.species_id.is_(None)).count())
print("5. Observations whose species_id does not exist:", db.query(Observation).filter(~Observation.species_id.in_(db.query(Species.id))).count())
print("6. Species with zero observations:", db.query(Species).filter(~Species.id.in_(db.query(Observation.species_id))).count())

# 7. Duplicate species based on normalized scientific_name
dups = db.query(func.lower(Species.scientific_name), func.count(Species.id)).group_by(func.lower(Species.scientific_name)).having(func.count(Species.id) > 1).all()
print("7. Duplicate species (scientific_name):", len(dups), dups)

# 8. Duplicate source records
dup_recs = db.query(Observation.source_id, Observation.latitude, Observation.longitude, Observation.observed_at, func.count(Observation.id)).group_by(Observation.source_id, Observation.latitude, Observation.longitude, Observation.observed_at).having(func.count(Observation.id) > 1).all()
print("8. Duplicate source records (source + lat/lon/time):", len(dup_recs))

# 9. Observation counts grouped by source
obs_by_src = db.query(DataSource.name, func.count(Observation.id)).join(Observation).group_by(DataSource.name).all()
print("9. Observation counts grouped by source:", obs_by_src)

# 10. Species counts grouped by source
sp_by_src = db.query(DataSource.name, func.count(distinct(Observation.species_id))).join(Observation).group_by(DataSource.name).all()
print("10. Species counts grouped by source:", sp_by_src)

print("11-13. eBird, GBIF, iNat species counts are included in #10 output")

print("14. Species with IUCN sis_id:", db.query(Species).filter(Species.iucn_sis_id.isnot(None)).count())
print("15. Species without IUCN sis_id:", db.query(Species).filter(Species.iucn_sis_id.is_(None)).count())

print("16. Observations with coordinates:", db.query(Observation).filter(Observation.latitude.isnot(None), Observation.longitude.isnot(None)).count())
print("17. Observations without coordinates:", db.query(Observation).filter((Observation.latitude.is_(None)) | (Observation.longitude.is_(None))).count())

# Also verify original 10 species still exist (check by id 1-10 or names)
orig_count = db.query(Species).filter(Species.id <= 10).count()
print("Original 10 species exist:", orig_count)

# Check Great Indian Bustard assignments
gib = db.query(Species).filter(Species.common_name == 'Great Indian Bustard').first()
if gib:
    gib_obs = db.query(DataSource.name, func.count(Observation.id)).join(Observation).filter(Observation.species_id == gib.id).group_by(DataSource.name).all()
    print("Great Indian Bustard obs by source:", gib_obs)
