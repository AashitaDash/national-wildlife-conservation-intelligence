#!/usr/bin/env python
"""
detailed_db_audit.py
====================
Deep audit of the PostgreSQL database before further expansion:
- Counts by taxonomic group (class), species, source, year, and region/bounding
- Identification of species with zero observations
- Identification of species with sparse (< 50 or < 100) or geographically concentrated observations
- Verification of data provenance and demonstration/synthetic markers
"""

import sys, os, json
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import SessionLocal
from backend.app.models.species import Species
from backend.app.models.observation import Observation, DataSource
from sqlalchemy import func, text, extract

def audit():
    db = SessionLocal()
    print("============================================================")
    print("        DETAILED PRE-EXPANSION AUDIT OF WILDLIFE DB         ")
    print("============================================================")

    # 1. Species and Observations Totals by Taxonomic Group
    species_by_class = dict(db.query(Species.class_name, func.count(Species.id)).group_by(Species.class_name).all())
    obs_by_class = dict(db.query(Species.class_name, func.count(Observation.id)).join(Observation, Observation.species_id == Species.id).group_by(Species.class_name).all())
    
    print("\n--- 1. Taxonomic Class Breakdown ---")
    for cls in ["Mammalia", "Reptilia", "Amphibia", "Aves"]:
        sp_c = species_by_class.get(cls, 0)
        ob_c = obs_by_class.get(cls, 0)
        avg = (ob_c / sp_c) if sp_c else 0
        print(f"  {cls:<10}: {sp_c:>3} species | {ob_c:>6} observations | avg {avg:>6.1f} obs/species")

    # 2. Breakdown by Data Source
    obs_by_src = db.query(DataSource.name, func.count(Observation.id)).join(Observation, Observation.source_id == DataSource.id).group_by(DataSource.name).all()
    print("\n--- 2. Observations by Data Source ---")
    for name, cnt in obs_by_src:
        print(f"  {name:<20}: {cnt:>6}")

    # 2b. Breakdown by Data Source across Classes
    obs_by_src_cls = db.query(Species.class_name, DataSource.name, func.count(Observation.id))\
        .join(Observation, Observation.species_id == Species.id)\
        .join(DataSource, Observation.source_id == DataSource.id)\
        .group_by(Species.class_name, DataSource.name).all()
    print("\n--- 2b. Source Breakdown by Taxonomic Class ---")
    cls_src_map = defaultdict(dict)
    for cls, src, cnt in obs_by_src_cls:
        cls_src_map[cls][src] = cnt
    for cls in ["Mammalia", "Reptilia", "Amphibia", "Aves"]:
        print(f"  {cls}: {dict(cls_src_map[cls])}")

    # 3. Observations by Year (non-avian vs avian)
    year_stats = db.query(
        extract('year', Observation.observed_at).label('year'),
        Species.class_name,
        func.count(Observation.id)
    ).join(Species, Observation.species_id == Species.id)\
     .group_by('year', Species.class_name)\
     .order_by('year')\
     .all()

    year_summary = defaultdict(lambda: defaultdict(int))
    for yr, cls, cnt in year_stats:
        y_int = int(yr) if yr else 0
        year_summary[y_int][cls] += cnt

    print("\n--- 3. Year Distribution (Sample Recent & Historic) ---")
    sorted_years = sorted(year_summary.keys())
    # print summary of years
    recent_years = [y for y in sorted_years if y >= 2015]
    print("  Recent Years (2015-2026):")
    for y in recent_years[-10:]:
        print(f"    Year {y}: Mammalia={year_summary[y]['Mammalia']}, Reptilia={year_summary[y]['Reptilia']}, Amphibia={year_summary[y]['Amphibia']}, Aves={year_summary[y]['Aves']}")
    older_cnt = sum(sum(year_summary[y].values()) for y in sorted_years if y < 2015)
    print(f"  Total observations from before 2015: {older_cnt}")

    # 4. Zero Observation Species
    all_species = db.query(Species).all()
    sp_obs_count = dict(db.query(Observation.species_id, func.count(Observation.id)).group_by(Observation.species_id).all())
    
    zero_obs = [s for s in all_species if sp_obs_count.get(s.id, 0) == 0]
    print(f"\n--- 4. Species with 0 Observations ({len(zero_obs)} total) ---")
    for s in zero_obs:
        print(f"  [ID {s.id}] {s.class_name}: {s.scientific_name} ({s.common_name})")

    # 5. Sparse Non-Avian Species (< 100 observations)
    non_avian_species = [s for s in all_species if s.class_name in ("Mammalia", "Reptilia", "Amphibia")]
    sparse_species = [s for s in non_avian_species if sp_obs_count.get(s.id, 0) < 100]
    
    print(f"\n--- 5. Non-Avian Species with < 100 Observations ({len(sparse_species)} of {len(non_avian_species)}) ---")
    sparse_by_class = defaultdict(list)
    for s in sparse_species:
        cnt = sp_obs_count.get(s.id, 0)
        sparse_by_class[s.class_name].append((s, cnt))
    
    for cls in ["Mammalia", "Reptilia", "Amphibia"]:
        print(f"  Class {cls} ({len(sparse_by_class[cls])} species):")
        for s, cnt in sorted(sparse_by_class[cls], key=lambda x: x[1]):
            # check geographic spread for sparse species
            obs_records = db.query(Observation.latitude, Observation.longitude).filter(Observation.species_id == s.id).all()
            if obs_records:
                lats = [r[0] for r in obs_records if r[0] is not None]
                lons = [r[1] for r in obs_records if r[1] is not None]
                clusters = len(set(round(lat, 1) for lat in lats))
                geo_info = f"lat:[{min(lats):.1f}, {max(lats):.1f}] lon:[{min(lons):.1f}, {max(lons):.1f}] clusters:{clusters}"
            else:
                geo_info = "no coords"
            print(f"    - ID {s.id:>3}: {s.scientific_name:<30} ({cnt:>2} obs) -> {geo_info}")

    # 6. Check for demonstration or synthetic markers
    demo_markers = db.query(Observation.id, Observation.notes, Observation.raw_metadata).filter(
        (Observation.notes.ilike('%demo%')) | 
        (Observation.notes.ilike('%synthetic%')) |
        (Observation.notes.ilike('%simulation%')) |
        (Observation.notes.ilike('%fallback%'))
    ).all()
    print(f"\n--- 6. Demonstration / Synthetic Markers ---")
    print(f"  Observations with demo/synthetic/simulation/fallback in notes: {len(demo_markers)}")
    for o_id, notes, meta in demo_markers:
        safe_note = (notes or "")[:100].encode('ascii', errors='replace').decode('ascii')
        print(f"    - Obs ID {o_id}: {safe_note}")

    # 7. Check location / state assignment in DB
    loc_count = db.query(func.count(Observation.id)).filter(Observation.location_id.isnot(None)).scalar()
    print(f"\n--- 7. Geographic Location Linkage ---")
    print(f"  Observations linked to location_id: {loc_count} / {db.query(Observation).count()}")

    db.close()

if __name__ == "__main__":
    audit()
