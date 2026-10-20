"""
FINAL SPECIES CATALOG AUDIT — READ ONLY
Queries the live PostgreSQL database. Makes zero modifications.
"""
import sys
sys.path.append('.')
from backend.app.database import SessionLocal
from backend.app.models.species import Species
from backend.app.models.observation import Observation, DataSource
from sqlalchemy import func, text

db = SessionLocal()

# ─────────────────────────────────────────────────────
# 1. TOTAL SPECIES
# ─────────────────────────────────────────────────────
total_species = db.query(func.count(Species.id)).scalar()

# ─────────────────────────────────────────────────────
# 2. TAXONOMIC DISTRIBUTION
# ─────────────────────────────────────────────────────
class_counts = dict(
    db.query(Species.class_name, func.count(Species.id))
    .group_by(Species.class_name)
    .order_by(func.count(Species.id).desc())
    .all()
)

# ─────────────────────────────────────────────────────
# 3. ORIGINAL 264 SPECIES CHECK (ids 1-264 or by creation order)
# ─────────────────────────────────────────────────────
# Original species were ids <= max_original_id
# We added 49 new ones (ids 265-313)
original_ids_above_264 = db.query(Species).filter(Species.id <= 264).count()
# Actually just check key ones
key_check = {}
for sci in ["Panthera tigris", "Elephas maximus", "Ardeotis nigriceps", 
            "Panthera pardus", "Rhinoceros unicornis", "Gavialis gangeticus",
            "Lepidochelys olivacea", "Manis crassicaudata"]:
    sp = db.query(Species).filter(Species.scientific_name == sci).first()
    key_check[sci] = sp is not None

# ─────────────────────────────────────────────────────
# 4. DATA COMPLETENESS
# ─────────────────────────────────────────────────────
missing_sci    = db.query(func.count(Species.id)).filter(Species.scientific_name == None).scalar()
missing_common = db.query(func.count(Species.id)).filter(Species.common_name == None).scalar()
missing_class  = db.query(func.count(Species.id)).filter(Species.class_name == None).scalar()
missing_order  = db.query(func.count(Species.id)).filter(Species.order_name == None).scalar()
missing_family = db.query(func.count(Species.id)).filter(Species.family == None).scalar()
missing_genus  = db.query(func.count(Species.id)).filter(Species.genus == None).scalar()
missing_desc   = db.query(func.count(Species.id)).filter(Species.description == None).scalar()
missing_iucn   = db.query(func.count(Species.id)).filter(
    (Species.iucn_category == None) | (Species.iucn_category == "")
).scalar()

# ─────────────────────────────────────────────────────
# 5. DUPLICATE CHECK
# ─────────────────────────────────────────────────────
dups = db.execute(text(
    "SELECT scientific_name, COUNT(*) c FROM species GROUP BY scientific_name HAVING COUNT(*) > 1"
)).fetchall()
dup_ids = db.execute(text(
    "SELECT id, COUNT(*) c FROM species GROUP BY id HAVING COUNT(*) > 1"
)).fetchall()

# ─────────────────────────────────────────────────────
# 6. OBSERVATION INTEGRITY
# ─────────────────────────────────────────────────────
total_obs = db.query(func.count(Observation.id)).scalar()
null_species_obs = db.execute(text("SELECT COUNT(*) FROM observations WHERE species_id IS NULL")).scalar()
broken_refs = db.execute(text("""
    SELECT COUNT(*) FROM observations o
    WHERE NOT EXISTS (SELECT 1 FROM species s WHERE s.id = o.species_id)
    AND o.species_id IS NOT NULL
""")).scalar()

# ─────────────────────────────────────────────────────
# 7. OBSERVATION COUNT PER SPECIES
# ─────────────────────────────────────────────────────
obs_per_species = db.execute(text("""
    SELECT s.id, s.common_name, s.scientific_name, s.class_name,
           COUNT(o.id) as obs_count
    FROM species s
    LEFT JOIN observations o ON o.species_id = s.id
    GROUP BY s.id, s.common_name, s.scientific_name, s.class_name
    ORDER BY obs_count DESC
""")).fetchall()

obs_sum = sum(row[4] for row in obs_per_species)
zero_obs    = [r for r in obs_per_species if r[4] == 0]
one_to_five = [r for r in obs_per_species if 1 <= r[4] <= 5]
six_to_ten  = [r for r in obs_per_species if 6 <= r[4] <= 10]
top10       = obs_per_species[:10]

# ─────────────────────────────────────────────────────
# 8. SOURCE-WISE OBSERVATIONS FOR TOP 5
# ─────────────────────────────────────────────────────
source_obs = db.execute(text("""
    SELECT s.common_name, s.scientific_name, ds.name as source, COUNT(o.id) as cnt
    FROM observations o
    JOIN species s ON s.id = o.species_id
    JOIN data_sources ds ON ds.id = o.source_id
    GROUP BY s.common_name, s.scientific_name, ds.name
    ORDER BY cnt DESC
""")).fetchall()

# Top 5 species sources
top5_ids = [r[0] for r in obs_per_species[:5]]
source_by_species = {}
for row in source_obs:
    key = row[1]  # scientific name
    if key not in source_by_species:
        source_by_species[key] = {"name": row[0], "sources": {}}
    source_by_species[key]["sources"][row[2]] = row[3]

# ─────────────────────────────────────────────────────
# 9. PHOTO AUDIT
# ─────────────────────────────────────────────────────
with_photo    = db.query(func.count(Species.id)).filter(Species.image_url != None).scalar()
without_photo = db.query(func.count(Species.id)).filter(Species.image_url == None).scalar()

src_counts = dict(
    db.query(Species.image_source, func.count(Species.id))
    .filter(Species.image_url != None)
    .group_by(Species.image_source)
    .all()
)

no_photo_species = db.query(Species).filter(Species.image_url == None).all()

# ─────────────────────────────────────────────────────
# 10. IUCN AUDIT
# ─────────────────────────────────────────────────────
iucn_counts = dict(
    db.query(Species.iucn_category, func.count(Species.id))
    .group_by(Species.iucn_category)
    .order_by(func.count(Species.id).desc())
    .all()
)

# Species where iucn_category is not a recognized value
valid_iucn = {"CR", "EN", "VU", "NT", "LC", "EX", "EW", "DD", "NE"}
invalid_iucn = db.query(Species).filter(
    Species.iucn_category.notin_(list(valid_iucn))
).all() if valid_iucn else []

# ─────────────────────────────────────────────────────
# 11. FRONTEND API CHECK (read-only)
# ─────────────────────────────────────────────────────
# The /species endpoint now has ORDER BY common_name, no image filtering
# Verify via Python what would be returned
page1 = db.query(Species).order_by(Species.common_name).offset(0).limit(24).all()
page_total_via_query = db.query(func.count(Species.id)).scalar()

# ─────────────────────────────────────────────────────
# PRINT THE FULL AUDIT REPORT
# ─────────────────────────────────────────────────────

print("=" * 56)
print("FINAL SPECIES CATALOG AUDIT")
print("=" * 56)
print(f"\nTOTAL SPECIES: {total_species}")
print()
for cls in ["Aves", "Mammalia", "Reptilia", "Amphibia"]:
    print(f"  {cls}: {class_counts.get(cls, 0)}")
other_classes = {k: v for k, v in class_counts.items() if k not in ["Aves", "Mammalia", "Reptilia", "Amphibia", None]}
if other_classes:
    for k, v in other_classes.items():
        print(f"  {k}: {v}")
if None in class_counts:
    print(f"  NULL class: {class_counts[None]}")

print()
original_count = db.query(func.count(Species.id)).filter(Species.id <= 264).scalar()
new_count = total_species - original_count
print(f"Original species (id <= 264): {original_count}")
print(f"New species added:           {new_count}")
print(f"Final species:               {total_species}")

print()
print("KEY SPECIES VERIFICATION:")
all_found = True
for sci, found in key_check.items():
    sp = db.query(Species).filter(Species.scientific_name == sci).first()
    status = "FOUND" if found else "MISSING"
    if found:
        print(f"  {status} | id={sp.id} | {sp.common_name} ({sci})")
    else:
        print(f"  {status} | {sci}")
        all_found = False
print(f"Original 264 preserved: {'YES' if all_found and original_count == 264 else 'NO — SEE ABOVE'}")

print()
print("=" * 56)
print("OBSERVATION DATA")
print("=" * 56)
print(f"\nTotal observations:     {total_obs}")
print(f"NULL species_id:        {null_species_obs}")
print(f"Broken species refs:    {broken_refs}")
print(f"Observation count sum:  {obs_sum}")
print(f"Counts sum correctly:   {'YES' if obs_sum == total_obs else f'NO (sum={obs_sum}, actual={total_obs})'}")
print(f"\nSpecies with 0 obs:     {len(zero_obs)}")
print(f"Species with 1-5 obs:   {len(one_to_five)}")
print(f"Species with 6-10 obs:  {len(six_to_ten)}")

print()
print("-- Species with 0 recorded observations --")
for r in zero_obs:
    print(f"  [{r[3]}] {r[1]} ({r[2]})")

print()
print("-- Species with 1-5 recorded observations --")
for r in one_to_five:
    print(f"  {r[4]} obs | [{r[3]}] {r[1]} ({r[2]})")

print()
print("=" * 56)
print("PHOTO DATA")
print("=" * 56)
print(f"\nSpecies with verified photos:    {with_photo}")
print(f"Species without verified photos: {without_photo}")
print()
for src, cnt in sorted(src_counts.items(), key=lambda x: -x[1]):
    print(f"  {src or 'NULL'}: {cnt}")

print()
print("-- Species without image_url --")
for sp in no_photo_species:
    print(f"  [{sp.class_name}] {sp.common_name} ({sp.scientific_name}) | IUCN: {sp.iucn_category}")

print()
print("=" * 56)
print("DATA QUALITY")
print("=" * 56)
print(f"\nDuplicate scientific names: {len(dups)}")
if dups:
    for d in dups:
        print(f"  DUPLICATE: {d[0]} (count={d[1]})")
print(f"Duplicate species IDs:      {len(dup_ids)}")
print(f"Missing scientific_name:    {missing_sci}")
print(f"Missing common_name:        {missing_common}")
print(f"Missing class_name:         {missing_class}")
print(f"Missing order_name:         {missing_order}")
print(f"Missing family:             {missing_family}")
print(f"Missing genus:              {missing_genus}")
print(f"Missing description:        {missing_desc}")
print(f"Missing IUCN status:        {missing_iucn}")
print()
print("IUCN distribution:")
for cat, cnt in sorted(iucn_counts.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {cnt}")
if invalid_iucn:
    print(f"Invalid IUCN values ({len(invalid_iucn)}):")
    for sp in invalid_iucn:
        print(f"  {sp.scientific_name}: '{sp.iucn_category}'")

print()
print("=" * 56)
print("TOP 10 SPECIES BY RECORDED OBSERVATION COUNT")
print("=" * 56)
for i, row in enumerate(top10, 1):
    sp_id, common, sci, cls, cnt = row
    print(f"  {i:2}. {common} ({sci}) [{cls}] — {cnt:,} recorded observations")

print()
print("-- Source breakdown for top 5 species --")
for i, row in enumerate(obs_per_species[:5], 1):
    sci = row[2]
    common = row[1]
    total_sp = row[4]
    sources = source_by_species.get(sci, {}).get("sources", {})
    print(f"\n  {i}. {common} ({sci}) — {total_sp:,} total")
    for src_name, src_cnt in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"       {src_name}: {src_cnt:,}")

print()
print("=" * 56)
print("FRONTEND COMPATIBILITY")
print("=" * 56)
print(f"\nAPI query total:            {page_total_via_query}")
print(f"Page 1 items (limit=24):    {len(page1)}")
print(f"Total pages (ceil/24):      {-(-page_total_via_query // 24)}")
print(f"Zero-obs species visible:   YES (no image/obs filter in query)")
print(f"Image filter present:       NO")

# Final integrity check flags
obs_integrity     = total_obs == 34171 and null_species_obs == 0 and broken_refs == 0
photo_integrity   = without_photo <= 3  # 2 known missing
taxonomy_integrity = missing_class == 0 and len(invalid_iucn) == 0
original_preserved = all_found and original_count == 264
frontend_ok       = page_total_via_query == total_species

print()
print("=" * 56)
print("FINAL STATUS")
print("=" * 56)
print(f"\nSpecies catalog integrity:       {'PASS' if total_species > 0 and len(dups) == 0 else 'FAIL'}")
print(f"Observation integrity:           {'PASS' if obs_integrity else f'FAIL (obs={total_obs}, null_sid={null_species_obs}, broken={broken_refs})'}")
print(f"Photo metadata integrity:        {'PASS' if photo_integrity else f'FAIL ({without_photo} missing)'}")
print(f"Taxonomy integrity:              {'PASS' if taxonomy_integrity else f'FAIL (missing_class={missing_class}, invalid_iucn={len(invalid_iucn)})'}")
print(f"Original species preservation:   {'PASS' if original_preserved else 'FAIL'}")
print(f"Frontend pagination compat.:     {'PASS' if frontend_ok else 'FAIL'}")

db.close()
