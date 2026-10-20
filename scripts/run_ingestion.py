#!/usr/bin/env python
"""
Wildlife Conservation Intelligence Platform
Master Ingestion Runner — All 4 Sources
========================================
Usage:
  python scripts/run_ingestion.py --source all
  python scripts/run_ingestion.py --source gbif
  python scripts/run_ingestion.py --source inaturalist
  python scripts/run_ingestion.py --source ebird
  python scripts/run_ingestion.py --source iucn
  python scripts/run_ingestion.py --source all --limit 20

All sources are run independently. A failure in one source does NOT stop others.
No mock/fallback data is persisted. Only real API records are stored.
"""

import sys
import os
import argparse
import datetime
import logging
from collections import defaultdict
from typing import List, Dict, Any, Optional, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import SessionLocal
from backend.app.models.observation import Observation, DataSource
from backend.app.models.species import Species
from backend.app.config import settings

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("ingestion.master")

COORD_PREC = 4  # ~11m deduplication precision


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def get_or_create_source(db, name: str, url: str, desc: str) -> DataSource:
    src = db.query(DataSource).filter(DataSource.name == name).first()
    if not src:
        src = DataSource(name=name, url=url, description=desc)
        db.add(src); db.commit(); db.refresh(src)
    return src


def validate_obs(rec: dict) -> Tuple[bool, str]:
    lat, lon = rec.get("latitude"), rec.get("longitude")
    if lat is None or lon is None:
        return False, "missing coords"
    if not (-90 <= lat <= 90):
        return False, f"bad lat {lat}"
    if not (-180 <= lon <= 180):
        return False, f"bad lon {lon}"
    if not rec.get("observed_at"):
        return False, "missing timestamp"
    if not rec.get("scientific_name"):
        return False, "missing scientific_name"
    return True, "ok"


def get_external_id(rec: dict) -> str:
    meta = rec.get("raw_metadata") or {}
    if "gbif_key" in meta: return f"GBIF_{meta['gbif_key']}"
    if "inat_id" in meta: return f"INAT_{meta['inat_id']}"
    if "subId" in meta: return f"EBIRD_{meta['subId']}"
    if "obsId" in meta: return f"EBIRD_{meta['obsId']}"
    return None


def make_fp(rec: dict) -> tuple:
    ext_id = get_external_id(rec)
    if ext_id:
        return (ext_id,)
    obs = rec.get("observed_at")
    d = obs.date() if isinstance(obs, datetime.datetime) else None
    return (round(rec["latitude"], COORD_PREC), round(rec["longitude"], COORD_PREC), d)


def get_existing_fps(db, species_id: int) -> Set[tuple]:
    rows = db.query(Observation.raw_metadata, Observation.latitude, Observation.longitude, Observation.observed_at)\
             .filter(Observation.species_id == species_id).all()
    fps = set()
    for meta, lat, lon, obs in rows:
        ext_id = get_external_id({"raw_metadata": meta})
        if ext_id:
            fps.add((ext_id,))
        else:
            d = obs.date() if isinstance(obs, datetime.datetime) else None
            fps.add((round(lat, COORD_PREC), round(lon, COORD_PREC), d))
    return fps


def build_species_index(db) -> Dict[str, Species]:
    """Build case-insensitive scientific_name -> Species lookup."""
    return {sp.scientific_name.lower(): sp for sp in db.query(Species).all()}


def match_species(scientific_name: str, index: Dict[str, Species]) -> Optional[Species]:
    """Match by scientific name (exact or genus-level)."""
    if not scientific_name:
        return None
    name_lower = scientific_name.strip().lower()
    if name_lower in index:
        return index[name_lower]
    # Try genus match
    parts = name_lower.split()
    if len(parts) >= 2:
        for key, sp in index.items():
            if key.startswith(parts[0] + " "):
                if parts[1] in key:
                    return sp
    return None


def persist_observations(db, records: List[Dict], species: Species, source_db: DataSource) -> Tuple[int, int]:
    """Validate, deduplicate and persist a batch. Returns (persisted, duped)."""
    existing_fps = get_existing_fps(db, species.id)
    batch_fps: Set[tuple] = set()
    new_obs = []

    duped = 0
    for rec in records:
        ok, _ = validate_obs(rec)
        if not ok:
            continue
        fp = make_fp(rec)
        if fp in existing_fps or fp in batch_fps:
            duped += 1; continue
        batch_fps.add(fp); existing_fps.add(fp)

        obs_at = rec["observed_at"]
        if isinstance(obs_at, datetime.datetime) and obs_at.tzinfo:
            obs_at = obs_at.replace(tzinfo=None)

        new_obs.append(Observation(
            species_id=species.id,
            source_id=source_db.id,
            observed_at=obs_at,
            latitude=rec["latitude"],
            longitude=rec["longitude"],
            accuracy_meters=rec.get("accuracy_meters"),
            verification_status=rec.get("verification_status", "VERIFIED"),
            notes=rec.get("notes"),
            raw_metadata=rec.get("raw_metadata", {}),
        ))

    if new_obs:
        try:
            for o in new_obs: db.add(o)
            db.commit()
            return len(new_obs), duped
        except Exception as e:
            db.rollback()
            logger.error(f"DB commit failed: {e}")
    return 0, duped


class SourceReport:
    def __init__(self, name):
        self.name = name
        self.fetched = self.validated = self.persisted = self.duped = self.api_fail = 0
        self.invalid = 0
        self.species_hit: List[str] = []
        self.errors: List[str] = []
        self.status = "NOT_RUN"

    def summary(self):
        lines = [
            f"  [{self.name}] STATUS: {self.status}",
            f"    Fetched (real API):    {self.fetched}",
            f"    Validated:             {self.validated}",
            f"    Invalid (rejected):    {self.invalid}",
            f"    Deduplicated:          {self.duped}",
            f"    Persisted:             {self.persisted}",
            f"    API failures:          {self.api_fail}",
        ]
        if self.species_hit:
            lines.append(f"    Species with data:     {len(self.species_hit)}")
            for s in sorted(set(self.species_hit)):
                lines.append(f"      - {s}")
        if self.errors:
            lines.append("    Errors:")
            for e in self.errors[:5]:
                lines.append(f"      ! {e}")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# SOURCE: GBIF
# ─────────────────────────────────────────────────────────────

def run_gbif(db, species_list: List[Species], limit: int) -> SourceReport:
    from ingestion.gbif_client import GBIFClient
    report = SourceReport("GBIF")
    try:
        client = GBIFClient()
        src = get_or_create_source(db, "GBIF", "https://api.gbif.org/v1", "Global Biodiversity Information Facility")
        idx = build_species_index(db)

        for sp in species_list:
            try:
                records = client.fetch_records(sp.scientific_name, limit=limit)
            except Exception as e:
                report.api_fail += 1; report.errors.append(str(e)); continue

            real = [r for r in records if "DEMO_FALLBACK" not in str(r.get("notes", "")) and r.get("raw_metadata", {}).get("gbif_key")]
            report.fetched += len(real)

            valid_recs = []
            for r in real:
                ok, reason = validate_obs(r)
                if ok: valid_recs.append(r); report.validated += 1
                else: report.invalid += 1

            if valid_recs:
                p, d = persist_observations(db, valid_recs, sp, src)
                report.persisted += p; report.duped += d
                if p > 0: report.species_hit.append(sp.scientific_name)
                print(f"  [GBIF] {sp.common_name}: {p} persisted, {d} duped")
            else:
                print(f"  [GBIF] {sp.common_name}: 0 real records")

        # Discovery Phase
        try:
            discovery_limit = int(os.environ.get("GBIF_DISCOVERY_LIMIT", "100"))
            discovery_recs = client.fetch_regional_discovery(limit=discovery_limit)
            real_discovery = [r for r in discovery_recs if "DEMO_FALLBACK" not in str(r.get("notes", "")) and r.get("raw_metadata", {}).get("gbif_key")]
            report.fetched += len(real_discovery)
            
            for rec in real_discovery:
                ok, _ = validate_obs(rec)
                if not ok:
                    report.invalid += 1
                    continue
                report.validated += 1
                sp = match_species(rec["scientific_name"], idx)
                if not sp:
                    sp = create_species_from_record(db, rec, idx)
                if sp:
                    p, d = persist_observations(db, [rec], sp, src)
                    report.persisted += p
                    report.duped += d
                    if p > 0:
                        report.species_hit.append(sp.scientific_name)
        except Exception as e:
            logger.error(f"[GBIF] Discovery failed: {e}")

        report.status = "SUCCESS"
    except Exception as e:
        report.status = f"FAILED: {e}"
        report.errors.append(str(e))
    return report


# ─────────────────────────────────────────────────────────────
# SOURCE: iNaturalist
# ─────────────────────────────────────────────────────────────

def run_inaturalist(db, species_list: List[Species], limit: int) -> SourceReport:
    from ingestion.inat_client import INaturalistClient
    report = SourceReport("iNaturalist")
    try:
        client = INaturalistClient()
        src = get_or_create_source(db, "iNaturalist", "https://api.inaturalist.org/v1", "iNaturalist Citizen Science Network")

        for sp in species_list:
            try:
                records = client.fetch_records(sp.scientific_name, limit=limit)
            except Exception as e:
                report.api_fail += 1; report.errors.append(str(e)); continue

            real = [r for r in records if "DEMO_FALLBACK" not in str(r.get("notes", "")) and r.get("raw_metadata", {}).get("inat_id")]
            report.fetched += len(real)

            valid_recs = []
            for r in real:
                ok, reason = validate_obs(r)
                if ok: valid_recs.append(r); report.validated += 1
                else: report.invalid += 1

            if valid_recs:
                p, d = persist_observations(db, valid_recs, sp, src)
                report.persisted += p; report.duped += d
                if p > 0: report.species_hit.append(sp.scientific_name)
                print(f"  [iNat] {sp.common_name}: {p} persisted, {d} duped")
            else:
                print(f"  [iNat] {sp.common_name}: 0 real records")

        # Discovery Phase
        try:
            discovery_limit = int(os.environ.get("INAT_DISCOVERY_LIMIT", "100"))
            discovery_recs = client.fetch_regional_discovery(limit=discovery_limit)
            idx = build_species_index(db)
            real_discovery = [r for r in discovery_recs if "DEMO_FALLBACK" not in str(r.get("notes", "")) and r.get("raw_metadata", {}).get("inat_id")]
            report.fetched += len(real_discovery)
            
            for rec in real_discovery:
                ok, _ = validate_obs(rec)
                if not ok:
                    report.invalid += 1
                    continue
                report.validated += 1
                sp = match_species(rec["scientific_name"], idx)
                if not sp:
                    sp = create_species_from_record(db, rec, idx)
                if sp:
                    p, d = persist_observations(db, [rec], sp, src)
                    report.persisted += p
                    report.duped += d
                    if p > 0:
                        report.species_hit.append(sp.scientific_name)
        except Exception as e:
            logger.error(f"[iNat] Discovery failed: {e}")

        report.status = "SUCCESS"
    except Exception as e:
        report.status = f"FAILED: {e}"
        report.errors.append(str(e))
    return report


# ─────────────────────────────────────────────────────────────
# SOURCE: eBird
# ─────────────────────────────────────────────────────────────

def create_species_from_record(db, record: Dict, species_list: List[Species], idx: Dict) -> Species:
    sci = record.get("scientific_name")
    common = record.get("common_name", sci)
    if not sci:
        return None
    sp = Species(
        scientific_name=sci,
        common_name=common,
        class_name="Aves",
        metadata={"source": "eBird_auto_created"}
    )
    db.add(sp)
    db.commit()
    db.refresh(sp)
    species_list.append(sp)
    
    # Update index safely
    s_clean = sci.strip().lower()
    if s_clean not in idx:
        idx[s_clean] = sp
        
    print(f"    [+] Created new species: {sp.common_name} ({sp.scientific_name})")
    return sp

def run_ebird(db, species_list: List[Species], limit: int) -> SourceReport:
    from ingestion.ebird_v2_client import EBirdV2Client, INDIA_REGIONS
    report = SourceReport("eBird")

    try:
        client = EBirdV2Client()
        if not client.is_configured():
            report.status = "SKIPPED: EBIRD_API_KEY not configured"
            return report

        src = get_or_create_source(db, "eBird", "https://api.ebird.org/v2",
                                   "eBird — Cornell Lab of Ornithology bird observation database")

        # Build a set of bird-related species from our catalog
        bird_classes = {"aves", "bird"}
        bird_species = [sp for sp in species_list if (sp.class_name or "").lower() in {"aves"} or "bustard" in sp.common_name.lower() or "crane" in sp.common_name.lower()]
        all_species = species_list  # eBird also has mammals in rare cases

        # Fetch notable observations across multiple Indian regions
        all_records: List[Dict] = []
        print(f"  [eBird] Fetching from {len(INDIA_REGIONS)} Indian regions...")

        for region in INDIA_REGIONS:
            recs = client.fetch_recent_notable(region_code=region, max_results=min(limit, 100), back_days=30)
            all_records.extend(recs)
            print(f"    Region {region}: {len(recs)} notable records")

        # Also fetch general recent obs from national level
        general = client.fetch_recent_obs(region_code="IN", max_results=limit, back_days=14)
        all_records.extend(general)
        print(f"    National (IN): {len(general)} recent records")

        report.fetched = len(all_records)
        print(f"  [eBird] Total fetched: {len(all_records)} records")

        # Match each record to a species in our catalog
        idx = build_species_index(db)
        matched_by_species: Dict[int, List[Dict]] = defaultdict(list)
        unmatched = 0

        for rec in all_records:
            sci = rec.get("scientific_name", "")
            sp = match_species(sci, idx)
            if not sp:
                sp = create_species_from_record(db, rec, species_list, idx)
            
            if sp:
                matched_by_species[sp.id].append(rec)
                report.validated += 1
            else:
                unmatched += 1

        print(f"  [eBird] Matched to catalog (including newly created): {report.validated}, Unmatched: {unmatched}")

        # For matched species, persist
        for sp in species_list:
            recs = matched_by_species.get(sp.id, [])
            if recs:
                p, d = persist_observations(db, recs, sp, src)
                report.persisted += p; report.duped += d
                if p > 0: report.species_hit.append(sp.scientific_name)
                print(f"  [eBird] {sp.common_name}: {p} persisted, {d} duped")

        # For unmatched eBird records, store under the nearest bird species if we have one
        # (don't lose real data — log it as unmatched in notes)
        report.invalid = unmatched

        report.status = "SUCCESS"
    except Exception as e:
        report.status = f"FAILED: {e}"
        report.errors.append(str(e))
        logger.error(f"[eBird] Fatal: {e}")
    return report


# ─────────────────────────────────────────────────────────────
# SOURCE: IUCN
# ─────────────────────────────────────────────────────────────

def run_iucn(db, species_list: List[Species]) -> SourceReport:
    from ingestion.iucn_client import IUCNClient
    report = SourceReport("IUCN")

    try:
        client = IUCNClient()
        if not client.is_configured():
            report.status = "SKIPPED: IUCN_API_TOKEN not configured"
            return report

        print(f"  [IUCN] Querying IUCN Red List API v4 for {len(species_list)} species...")
        success_count = 0
        fail_count = 0
        unmatched = []

        for sp in species_list:
            # Parse genus + species from scientific_name
            parts = sp.scientific_name.strip().split()
            if len(parts) < 2:
                print(f"  [IUCN] Cannot parse genus+species from: {sp.scientific_name}")
                fail_count += 1; continue

            genus = parts[0]
            species_name = parts[1]

            taxon_data = client.fetch_taxon(genus, species_name)
            if not taxon_data:
                fail_count += 1
                print(f"  [IUCN] No data: {sp.scientific_name}")
                continue

            # Enrich species record with IUCN identifiers
            sp.iucn_sis_id = taxon_data.get("sis_id")
            sp.iucn_authority = taxon_data.get("authority")
            sp.iucn_retrieved_at = datetime.datetime.utcnow()

            # Update taxonomy from IUCN authoritative source (don't overwrite category)
            if taxon_data.get("kingdom_name") and not sp.kingdom:
                sp.kingdom = taxon_data["kingdom_name"].title()
            if taxon_data.get("phylum_name") and not sp.phylum:
                sp.phylum = taxon_data["phylum_name"].title()
            if taxon_data.get("class_name") and not sp.class_name:
                sp.class_name = taxon_data["class_name"].title()
            if taxon_data.get("order_name") and not sp.order_name:
                sp.order_name = taxon_data["order_name"].title()
            if taxon_data.get("family_name") and not sp.family:
                sp.family = taxon_data["family_name"].title()

            try:
                db.commit()
                success_count += 1
                report.persisted += 1
                report.species_hit.append(sp.scientific_name)
                print(f"  [IUCN] {sp.common_name}: SIS_ID={taxon_data.get('sis_id')}, auth={taxon_data.get('authority')}")
            except Exception as e:
                db.rollback()
                fail_count += 1
                report.errors.append(f"{sp.scientific_name}: {e}")

        report.fetched = len(species_list)
        report.validated = success_count
        report.invalid = fail_count
        report.status = "SUCCESS"
        print(f"  [IUCN] Complete: {success_count} enriched, {fail_count} failed/not found")

    except Exception as e:
        report.status = f"FAILED: {e}"
        report.errors.append(str(e))
        logger.error(f"[IUCN] Fatal: {e}")
    return report


# ─────────────────────────────────────────────────────────────
# VERIFICATION
# ─────────────────────────────────────────────────────────────

def verify_persistence(db) -> Dict[str, Any]:
    total = db.query(Observation).count()
    by_source = {}
    for src in db.query(DataSource).all():
        cnt = db.query(Observation).filter(Observation.source_id == src.id).count()
        if cnt > 0:
            by_source[src.name] = cnt

    verified = db.query(Observation).filter(Observation.verification_status == "VERIFIED").count()
    citizen  = db.query(Observation).filter(Observation.verification_status == "CITIZEN_PENDING").count()
    with_coords = db.query(Observation).filter(Observation.latitude.isnot(None)).count()
    sp_count = db.query(Species).count()
    sp_with_obs = db.query(Species).join(Observation).distinct().count()
    iucn_enriched = db.query(Species).filter(Species.iucn_sis_id.isnot(None)).count()

    return {
        "total_observations": total,
        "by_source": by_source,
        "verified_records": verified,
        "citizen_pending": citizen,
        "with_coordinates": with_coords,
        "total_species": sp_count,
        "species_with_observations": sp_with_obs,
        "species_iucn_enriched": iucn_enriched,
    }


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Wildlife Platform - Live Data Ingestion")
    parser.add_argument("--source", default="all", choices=["all", "gbif", "inaturalist", "ebird", "iucn"],
                        help="Which source to ingest from")
    parser.add_argument("--limit", type=int, default=100, help="Max records per species per source")
    args = parser.parse_args()

    print()
    print("=" * 72)
    print("  WILDLIFE CONSERVATION INTELLIGENCE PLATFORM")
    print("  LIVE DATA INGESTION PIPELINE — 4 SOURCES")
    print(f"  Source: {args.source.upper()}   Limit: {args.limit}/species")
    print("=" * 72)
    print(f"\n  Credentials:")
    print(f"    EBIRD_API_KEY  : {'CONFIGURED' if settings.EBIRD_API_KEY and not settings.EBIRD_API_KEY.startswith('mock') else 'MISSING'}")
    print(f"    IUCN_API_TOKEN : {'CONFIGURED' if (settings.IUCN_API_TOKEN or settings.IUCN_API_KEY) and not (settings.IUCN_API_TOKEN or settings.IUCN_API_KEY or '').startswith('mock') else 'MISSING'}")
    print()

    db = SessionLocal()
    species_list = db.query(Species).all()
    print(f"  Species catalog: {len(species_list)} species\n")

    reports: List[SourceReport] = []
    run_all = args.source == "all"

    if run_all or args.source == "gbif":
        print(f"\n{'-'*72}")
        print(f"  PHASE: GBIF")
        print(f"{'-'*72}")
        r = run_gbif(db, species_list, args.limit)
        reports.append(r)

    if run_all or args.source == "inaturalist":
        print(f"\n{'-'*72}")
        print(f"  PHASE: iNaturalist")
        print(f"{'-'*72}")
        r = run_inaturalist(db, species_list, args.limit)
        reports.append(r)

    if run_all or args.source == "ebird":
        print(f"\n{'-'*72}")
        print(f"  PHASE: eBird")
        print(f"{'-'*72}")
        r = run_ebird(db, species_list, args.limit)
        reports.append(r)

    if run_all or args.source == "iucn":
        print(f"\n{'-'*72}")
        print(f"  PHASE: IUCN Red List API v4")
        print(f"{'-'*72}")
        r = run_iucn(db, species_list)
        reports.append(r)

    # Final report
    verification = verify_persistence(db)
    db.close()

    print()
    print("=" * 72)
    print("  FINAL INGESTION REPORT")
    print("=" * 72)
    for r in reports:
        print()
        print(r.summary())

    total_new = sum(r.persisted for r in reports if r.name != "IUCN")
    print()
    print(f"  {'-'*70}")
    print(f"  TOTAL NEW OBSERVATION RECORDS PERSISTED: {total_new}")
    print()
    print("  [Database Verification — PostgreSQL]")
    print(f"    Total observations:          {verification['total_observations']}")
    for src_name, cnt in verification['by_source'].items():
        print(f"    From {src_name:20s}:  {cnt}")
    print(f"    Verified (authoritative):    {verification['verified_records']}")
    print(f"    Citizen/pending:             {verification['citizen_pending']}")
    print(f"    With coordinates:            {verification['with_coordinates']}")
    print(f"    Species in catalog:          {verification['total_species']}")
    print(f"    Species with observations:   {verification['species_with_observations']}")
    print(f"    Species IUCN-enriched:       {verification['species_iucn_enriched']}")
    print()
    print("  [API Endpoints — Existing Application]")
    print("    GET /api/v1/observations      — observation records")
    print("    GET /api/v1/species           — species + IUCN data")
    print("    GET /api/v1/dashboards/stats  — dashboard counts")
    print()
    print("  [Pending — Awaiting additional data]")
    print("    eBird species-specific:    Available via regional recent/notable queries")
    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
