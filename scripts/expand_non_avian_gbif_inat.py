#!/usr/bin/env python
"""
expand_non_avian_gbif_inat.py
NON-AVIAN GEOGRAPHIC EXPANSION - Phase 1: Species + Real Observations

Strategy:
  1. Add new non-avian species not yet in the catalog
  2. For EVERY species (new + existing with 0 obs), fetch real GBIF and
     iNaturalist records with valid geographic coordinates
  3. Strict deduplication via source + source_record_id
  4. No fabricated coordinates - only real API data is persisted
  5. Fallback data explicitly tagged DEMO_FALLBACK is EXCLUDED

Usage:
  python scripts/expand_non_avian_gbif_inat.py
  python scripts/expand_non_avian_gbif_inat.py --dry-run
  python scripts/expand_non_avian_gbif_inat.py --limit 200
  python scripts/expand_non_avian_gbif_inat.py --source gbif
  python scripts/expand_non_avian_gbif_inat.py --source inat
"""

import sys, os, time, datetime, argparse, logging
from typing import List, Dict, Any, Optional, Set, Tuple
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from backend.app.database import SessionLocal
from backend.app.models.species import Species
from backend.app.models.observation import Observation, DataSource
from sqlalchemy import func

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("non_avian_expansion")

# -----------------------------------------------------------------------------
# SPECIES CATALOG - NEW ADDITIONS
# Format: (scientific_name, common_name, class_name, order_name, family,
#          genus, iucn_category, description)
# -----------------------------------------------------------------------------

NEW_SPECIES_CATALOG = [
    # MAMMALIA
    ("Axis axis","Chital","Mammalia","Artiodactyla","Cervidae","Axis","LC","Spotted deer endemic to the Indian subcontinent. Most common deer species in Indian forests and an important prey base for large predators."),
    ("Axis porcinus","Hog Deer","Mammalia","Artiodactyla","Cervidae","Axis","EN","Endangered stocky deer of riverine grasslands. Restricted to terai and Brahmaputra floodplains."),
    ("Bos mutus","Wild Yak","Mammalia","Artiodactyla","Bovidae","Bos","VU","Vulnerable large bovid of high-altitude Tibetan Plateau margins. Found in Ladakh, India."),
    ("Bubalus arnee","Wild Water Buffalo","Mammalia","Artiodactyla","Bovidae","Bubalus","EN","Endangered ancestor of domestic water buffalo. Small wild populations survive in Assam and Chhattisgarh."),
    ("Canis aureus","Golden Jackal","Mammalia","Carnivora","Canidae","Canis","LC","Widespread opportunistic omnivore found across India. Important scavenger and seed disperser."),
    ("Canis lupus pallipes","Indian Wolf","Mammalia","Carnivora","Canidae","Canis","EN","Endangered subspecies of grey wolf restricted to peninsular India."),
    ("Capra sibirica","Siberian Ibex","Mammalia","Artiodactyla","Bovidae","Capra","LC","Sure-footed wild goat of high alpine terrain in Ladakh and Himachal Pradesh."),
    ("Caracal caracal","Caracal","Mammalia","Carnivora","Felidae","Caracal","LC","Medium-sized wild cat with distinctive tufted ears. Found in arid scrublands of Rajasthan."),
    ("Felis chaus","Jungle Cat","Mammalia","Carnivora","Felidae","Felis","LC","India's most widespread small felid. Found in diverse habitats from mangroves to farmland."),
    ("Funambulus palmarum","Indian Palm Squirrel","Mammalia","Rodentia","Sciuridae","Funambulus","LC","Three-striped palm squirrel endemic to peninsular India and Sri Lanka."),
    ("Gazella bennettii","Chinkara","Mammalia","Artiodactyla","Bovidae","Gazella","LC","Indian gazelle found in arid and semi-arid grasslands. Extremely fast runner."),
    ("Herpestes edwardsii","Indian Grey Mongoose","Mammalia","Carnivora","Herpestidae","Herpestes","LC","Widespread mongoose species across the Indian subcontinent. Famous for snake-killing ability."),
    ("Herpestes smithii","Ruddy Mongoose","Mammalia","Carnivora","Herpestidae","Herpestes","LC","Endemic mongoose of peninsular India and Sri Lanka. Found in dry deciduous forests."),
    ("Hystrix indica","Indian Crested Porcupine","Mammalia","Rodentia","Hystricidae","Hystrix","LC","Largest rodent in India. Covered in sharp black and white quills used for defence."),
    ("Lepus nigricollis","Indian Hare","Mammalia","Lagomorpha","Leporidae","Lepus","LC","Common hare found throughout peninsular India and Sri Lanka. Nocturnal grazer."),
    ("Lutra lutra","Eurasian Otter","Mammalia","Carnivora","Mustelidae","Lutra","NT","Near Threatened semi-aquatic mammal distributed across India's river systems."),
    ("Macaca mulatta","Rhesus Macaque","Mammalia","Primates","Cercopithecidae","Macaca","LC","Highly adaptable macaque common across northern and central India."),
    ("Macaca radiata","Bonnet Macaque","Mammalia","Primates","Cercopithecidae","Macaca","LC","Endemic macaque of peninsular India named for the distinctive whorl of hair on its head."),
    ("Mellivora capensis","Honey Badger","Mammalia","Carnivora","Mustelidae","Mellivora","LC","Notoriously ferocious mustelid found in arid and semi-arid India."),
    ("Moschus leucogaster","Himalayan Musk Deer","Mammalia","Artiodactyla","Moschidae","Moschus","VU","Vulnerable primitive deer with sabre-like canine teeth instead of antlers."),
    ("Muntiacus muntjak","Indian Muntjac","Mammalia","Artiodactyla","Cervidae","Muntiacus","LC","Small barking deer found across diverse forest types. One of the world's oldest deer species."),
    ("Paradoxurus hermaphroditus","Common Palm Civet","Mammalia","Carnivora","Viverridae","Paradoxurus","LC","Nocturnal civet widespread across South and Southeast Asia. Important seed disperser."),
    ("Petaurista philippensis","Indian Giant Flying Squirrel","Mammalia","Rodentia","Sciuridae","Petaurista","LC","One of the world's largest gliding mammals; can glide up to 75 metres between trees."),
    ("Prionailurus bengalensis","Leopard Cat","Mammalia","Carnivora","Felidae","Prionailurus","LC","Small wild cat widespread across Asia. Ancestral species from which domestic Bengal cat was derived."),
    ("Pseudois nayaur","Blue Sheep","Mammalia","Artiodactyla","Bovidae","Pseudois","LC","High-altitude Himalayan ungulate that is prey to snow leopards."),
    ("Pteropus giganteus","Indian Flying Fox","Mammalia","Chiroptera","Pteropodidae","Pteropus","LC","Largest bat in India with wingspan up to 1.5 m. Important pollinator and seed disperser."),
    ("Ratufa indica","Indian Giant Squirrel","Mammalia","Rodentia","Sciuridae","Ratufa","LC","Colourful arboreal squirrel endemic to peninsular India. One of the world's largest squirrels."),
    ("Semnopithecus entellus","Grey Langur","Mammalia","Primates","Cercopithecidae","Semnopithecus","LC","Sacred monkey of Hindu tradition; most widespread primate in India."),
    ("Sousa chinensis","Indo-Pacific Humpback Dolphin","Mammalia","Artiodactyla","Delphinidae","Sousa","VU","Vulnerable coastal dolphin found in India's nearshore waters and estuaries."),
    ("Sus scrofa","Wild Boar","Mammalia","Artiodactyla","Suidae","Sus","LC","Ancestor of domestic pig; found across India in diverse habitats."),
    ("Ursus thibetanus","Himalayan Black Bear","Mammalia","Carnivora","Ursidae","Ursus","VU","Vulnerable bear of the Himalayas and Northeast India. Distinctive white chest-patch."),
    ("Viverricula indica","Small Indian Civet","Mammalia","Carnivora","Viverridae","Viverricula","LC","Nocturnal civet widespread across India. Feeds on small animals, birds and fruit."),
    ("Vulpes bengalensis","Bengal Fox","Mammalia","Carnivora","Canidae","Vulpes","LC","Endemic fox of the Indian subcontinent. Found in short open grasslands and scrublands."),
    # REPTILIA
    ("Calotes versicolor","Oriental Garden Lizard","Reptilia","Squamata","Agamidae","Calotes","LC","Common agamid lizard found across India. Males turn brilliant red-orange during breeding season."),
    ("Hemidactylus flaviviridis","Yellow-bellied House Gecko","Reptilia","Squamata","Gekkonidae","Hemidactylus","LC","Abundant gecko throughout India found in human habitations. Feeds on insects."),
    ("Melanochelys trijuga","Indian Black Turtle","Reptilia","Testudines","Geoemydidae","Melanochelys","VU","Vulnerable freshwater turtle found in rivers and ponds across peninsular India."),
    ("Ptyas mucosa","Indian Rat Snake","Reptilia","Squamata","Colubridae","Ptyas","LC","Large non-venomous snake widespread across India. Vital for rodent population control."),
    ("Trimeresurus gramineus","Bamboo Pit Viper","Reptilia","Squamata","Viperidae","Trimeresurus","LC","Green arboreal pit viper found across India's forested zones."),
    # AMPHIBIA
    ("Duttaphrynus melanostictus","Asian Common Toad","Amphibia","Anura","Bufonidae","Duttaphrynus","LC","Widespread toad found across India in varied habitats including urban areas."),
    ("Euphlyctis cyanophlyctis","Skittering Frog","Amphibia","Anura","Dicroglossidae","Euphlyctis","LC","Aquatic frog found in ponds and lakes across India. Excellent swimmer."),
    ("Hoplobatrachus tigerinus","Indian Bull Frog","Amphibia","Anura","Dicroglossidae","Hoplobatrachus","LC","India's largest frog; males turn bright yellow-green during monsoon breeding."),
    ("Ichthyophis bombayensis","Bombay Caecilian","Amphibia","Gymnophiona","Ichthyophiidae","Ichthyophis","LC","Limbless burrowing amphibian found in Mumbai region's laterite soils."),
    ("Nyctibatrachus humayuni","Humayun's Night Frog","Amphibia","Anura","Nyctibatrachidae","Nyctibatrachus","EN","Endangered nocturnal frog endemic to the northern Western Ghats."),
    ("Polypedates maculatus","Common Tree Frog","Amphibia","Anura","Rhacophoridae","Polypedates","LC","Arboreal foam-nesting frog common across India."),
    ("Ramanella obscura","Forest Narrow-mouthed Frog","Amphibia","Anura","Microhylidae","Ramanella","LC","Small terrestrial frog endemic to the Western Ghats."),
    ("Sphaerotheca breviceps","Indian Burrowing Frog","Amphibia","Anura","Dicroglossidae","Sphaerotheca","LC","Fossorial frog widespread across the Indian subcontinent. Emerges to breed in monsoon."),
    ("Uperodon systoma","Marbled Balloon Frog","Amphibia","Anura","Microhylidae","Uperodon","LC","Rotund burrowing frog of central and southern India. Breeds in temporary monsoon pools."),
]

GBIF_URL = "https://api.gbif.org/v1/occurrence/search"
INAT_URL = "https://api.inaturalist.org/v1/observations"
INDIA_PLACE_ID = 6681

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "WildlifeConservationPlatform/1.0 (academic research)"})


def valid_coord(lat: Any, lon: Any) -> bool:
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return False
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return False
    if lat == 0.0 and lon == 0.0:
        return False
    return True


def fetch_inat_photo(scientific_name: str, timeout: int = 10):
    try:
        params = {"taxon_name": scientific_name, "has[]": "photos",
                  "quality_grade": "research", "per_page": 5, "order_by": "votes"}
        r = SESSION.get(INAT_URL, params=params, timeout=timeout)
        if r.status_code != 200:
            return None, None, None
        genus = scientific_name.split()[0]
        for obs in r.json().get("results", []):
            if not obs.get("taxon", {}).get("name", "").startswith(genus):
                continue
            photos = obs.get("photos", [])
            if not photos:
                continue
            photo = photos[0]
            raw_url = photo.get("url", "")
            if not raw_url:
                continue
            photo_url = raw_url.replace("/square.", "/original.")
            try:
                head = SESSION.head(photo_url, timeout=6)
                if head.status_code == 200:
                    return photo_url, photo.get("license_code") or "all-rights-reserved", photo.get("attribution", "")
            except Exception:
                pass
    except Exception as e:
        logger.debug(f"iNat photo error for {scientific_name}: {e}")
    return None, None, None


def fetch_gbif_records(scientific_name: str, limit: int = 100, timeout: int = 15) -> List[Dict]:
    params = {"scientificName": scientific_name, "hasCoordinate": "true", "country": "IN", "limit": limit}
    try:
        r = SESSION.get(GBIF_URL, params=params, timeout=timeout)
        if r.status_code != 200:
            return []
        data = r.json()
    except Exception as e:
        logger.debug(f"GBIF fetch error for {scientific_name}: {e}")
        return []
    records = []
    for item in data.get("results", []):
        lat = item.get("decimalLatitude")
        lon = item.get("decimalLongitude")
        if not valid_coord(lat, lon):
            continue
        gbif_key = item.get("key")
        if not gbif_key:
            continue
        event_date = item.get("eventDate")
        try:
            obs_dt = datetime.datetime.fromisoformat(str(event_date).replace("Z", "+00:00")) if event_date else datetime.datetime.utcnow()
        except Exception:
            obs_dt = datetime.datetime.utcnow()
        if obs_dt.tzinfo:
            obs_dt = obs_dt.replace(tzinfo=None)
        records.append({
            "source": "GBIF", "scientific_name": scientific_name,
            "latitude": float(lat), "longitude": float(lon),
            "accuracy_meters": item.get("coordinateUncertaintyInMeters", 50.0),
            "observed_at": obs_dt, "verification_status": "VERIFIED",
            "notes": f"GBIF dataset: {item.get('datasetName', 'Field Observation')}",
            "raw_metadata": {"gbif_key": gbif_key, "basis_of_record": item.get("basisOfRecord"), "license": item.get("license")},
        })
    return records


def fetch_inat_records(scientific_name: str, limit: int = 100, timeout: int = 15) -> List[Dict]:
    params = {"taxon_name": scientific_name, "place_id": INDIA_PLACE_ID,
              "has[]": "geo", "per_page": min(limit, 200), "order": "desc", "order_by": "created_at"}
    try:
        r = SESSION.get(INAT_URL, params=params, timeout=timeout)
        if r.status_code != 200:
            return []
        data = r.json()
    except Exception as e:
        logger.debug(f"iNat fetch error for {scientific_name}: {e}")
        return []
    records = []
    for item in data.get("results", []):
        geojson = item.get("geojson")
        if not geojson or "coordinates" not in geojson:
            continue
        lon, lat = geojson["coordinates"]
        if not valid_coord(lat, lon):
            continue
        inat_id = item.get("id")
        if not inat_id:
            continue
        time_observed = item.get("time_observed_at") or item.get("observed_on")
        try:
            if time_observed and "T" in str(time_observed):
                obs_dt = datetime.datetime.fromisoformat(str(time_observed).replace("Z", "+00:00"))
            elif time_observed:
                obs_dt = datetime.datetime.strptime(str(time_observed), "%Y-%m-%d")
            else:
                obs_dt = datetime.datetime.utcnow()
        except Exception:
            obs_dt = datetime.datetime.utcnow()
        if hasattr(obs_dt, "tzinfo") and obs_dt.tzinfo:
            obs_dt = obs_dt.replace(tzinfo=None)
        quality = item.get("quality_grade", "casual")
        records.append({
            "source": "iNaturalist", "scientific_name": scientific_name,
            "latitude": float(lat), "longitude": float(lon),
            "accuracy_meters": item.get("positional_accuracy", 100.0),
            "observed_at": obs_dt,
            "verification_status": "VERIFIED" if quality == "research" else "CITIZEN_PENDING",
            "notes": f"iNaturalist community record ({quality}): {item.get('description') or 'Citizen observation'}",
            "raw_metadata": {"inat_id": inat_id, "quality_grade": quality,
                             "user": item.get("user", {}).get("login"),
                             "photos_count": len(item.get("photos", []))},
        })
    return records


COORD_PREC = 4

def make_fingerprint(rec: Dict) -> tuple:
    meta = rec.get("raw_metadata") or {}
    if meta.get("gbif_key"):
        return ("GBIF", str(meta["gbif_key"]))
    if meta.get("inat_id"):
        return ("INAT", str(meta["inat_id"]))
    obs = rec.get("observed_at")
    d = obs.date() if isinstance(obs, datetime.datetime) else None
    return ("COORD", round(rec["latitude"], COORD_PREC), round(rec["longitude"], COORD_PREC), d)


def get_existing_fingerprints(db, species_id: int) -> Set[tuple]:
    rows = db.query(Observation.raw_metadata, Observation.latitude,
                    Observation.longitude, Observation.observed_at).filter(
                        Observation.species_id == species_id).all()
    fps: Set[tuple] = set()
    for meta, lat, lon, obs in rows:
        m = meta or {}
        if m.get("gbif_key"):
            fps.add(("GBIF", str(m["gbif_key"])))
        elif m.get("inat_id"):
            fps.add(("INAT", str(m["inat_id"])))
        else:
            d = obs.date() if isinstance(obs, datetime.datetime) else None
            fps.add(("COORD", round(lat, COORD_PREC), round(lon, COORD_PREC), d))
    return fps


def get_or_create_source(db, name: str, url: str, desc: str) -> DataSource:
    src = db.query(DataSource).filter(DataSource.name == name).first()
    if not src:
        src = DataSource(name=name, url=url, description=desc)
        db.add(src); db.commit(); db.refresh(src)
    return src


def persist_records(db, records: List[Dict], species: Species, source_db: DataSource, dry_run: bool) -> Tuple[int, int]:
    existing_fps = get_existing_fingerprints(db, species.id)
    batch_fps: Set[tuple] = set()
    new_obs = []
    duped = 0
    for rec in records:
        fp = make_fingerprint(rec)
        if fp in existing_fps or fp in batch_fps:
            duped += 1; continue
        batch_fps.add(fp); existing_fps.add(fp)
        obs_at = rec["observed_at"]
        if isinstance(obs_at, datetime.datetime) and obs_at.tzinfo:
            obs_at = obs_at.replace(tzinfo=None)
        new_obs.append(Observation(
            species_id=species.id, source_id=source_db.id,
            observed_at=obs_at, latitude=rec["latitude"], longitude=rec["longitude"],
            accuracy_meters=rec.get("accuracy_meters"),
            verification_status=rec.get("verification_status", "VERIFIED"),
            notes=rec.get("notes"), raw_metadata=rec.get("raw_metadata", {}),
        ))
    if new_obs and not dry_run:
        try:
            for o in new_obs: db.add(o)
            db.commit()
            return len(new_obs), duped
        except Exception as e:
            db.rollback()
            logger.error(f"DB commit failed for {species.scientific_name}: {e}")
            return 0, duped
    elif new_obs and dry_run:
        return len(new_obs), duped
    return 0, duped


def main():
    parser = argparse.ArgumentParser(description="Non-Avian Geographic Expansion")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--source", choices=["gbif", "inat", "both"], default="both")
    parser.add_argument("--classes", nargs="+", default=["Mammalia", "Reptilia", "Amphibia"])
    parser.add_argument("--skip-obs", action="store_true")
    parser.add_argument("--new-only", action="store_true")
    parser.add_argument("--zero-obs-only", action="store_true", help="Fetch observations only for species with 0 observations")
    args = parser.parse_args()

    print("\n" + "=" * 72)
    print("  WILDLIFE CONSERVATION INTELLIGENCE PLATFORM")
    print("  NON-AVIAN GEOGRAPHIC EXPANSION - GBIF + iNaturalist")
    print(f"  Limit: {args.limit}/species  Source: {args.source.upper()}  Dry-run: {args.dry_run}")
    print("=" * 72)

    db = SessionLocal()
    before_species = db.query(Species).count()
    before_obs = db.query(Observation).count()
    before_by_class = dict(db.query(Species.class_name, func.count(Species.id)).group_by(Species.class_name).all())
    print(f"\n  BEFORE: Species={before_species}  Observations={before_obs}")
    for cls, cnt in sorted(before_by_class.items()):
        print(f"    {cls}: {cnt}")

    gbif_src = get_or_create_source(db, "GBIF", "https://api.gbif.org/v1", "Global Biodiversity Information Facility")
    inat_src = get_or_create_source(db, "iNaturalist", "https://api.inaturalist.org/v1", "iNaturalist Citizen Science Network")
    existing_names = {sp.scientific_name.lower() for sp in db.query(Species.scientific_name).all()}
    target_classes = set(args.classes)

    print(f"\n{'-'*72}\n  PHASE 1: SPECIES CATALOG EXPANSION\n{'-'*72}")
    added_species_ids: List[int] = []
    skipped = 0
    new_count = 0

    for row in NEW_SPECIES_CATALOG:
        sci, common, cls, order, family, genus, iucn, desc = row
        if cls not in target_classes:
            continue
        if sci.lower() in existing_names:
            skipped += 1; continue
        photo_url, lic, attr = None, None, None
        if not args.dry_run:
            photo_url, lic, attr = fetch_inat_photo(sci)
            time.sleep(0.5)
        sp = Species(scientific_name=sci, common_name=common, class_name=cls,
                     order_name=order, family=family, genus=genus,
                     iucn_category=iucn, description=desc, image_url=photo_url,
                     image_source="iNaturalist" if photo_url else None,
                     image_license=lic, image_attribution=attr)
        if not args.dry_run:
            db.add(sp); db.commit(); db.refresh(sp)
            added_species_ids.append(sp.id)
            existing_names.add(sci.lower())
        new_count += 1
        tag = "[PHOTO]" if photo_url else "[NO PHOTO]"
        print(f"  + {sci} / {common} {tag}")

    print(f"\n  New species added: {new_count}  |  Skipped (exist): {skipped}")

    if args.skip_obs:
        print("\n  --skip-obs flag set. Skipping observation fetch.")
        db.close(); return

    print(f"\n{'-'*72}\n  PHASE 2: REAL OBSERVATION FETCH\n{'-'*72}")
    all_target_species = db.query(Species).filter(Species.class_name.in_(list(target_classes))).all()
    if args.new_only:
        target_species = [sp for sp in all_target_species if sp.id in set(added_species_ids)]
    elif args.zero_obs_only:
        zero_ids = {s.id for s in all_target_species if db.query(Observation.id).filter(Observation.species_id == s.id).first() is None}
        target_species = [sp for sp in all_target_species if sp.id in zero_ids]
    else:
        target_species = all_target_species
    print(f"  Processing {len(target_species)} species...")

    gbif_fetched = gbif_persisted = gbif_duped = 0
    inat_fetched = inat_persisted = inat_duped = 0
    species_with_obs = []
    species_no_coords = []

    for i, sp in enumerate(target_species, 1):
        prefix = f"  [{i:3d}/{len(target_species)}] {sp.scientific_name}"
        sp_total = 0
        gbif_recs = []
        inat_recs = []

        if args.source in ("gbif", "both"):
            gbif_recs = fetch_gbif_records(sp.scientific_name, limit=args.limit)
            gbif_fetched += len(gbif_recs)
            if gbif_recs:
                p, d = persist_records(db, gbif_recs, sp, gbif_src, args.dry_run)
                gbif_persisted += p; gbif_duped += d; sp_total += p
                print(f"{prefix} | GBIF: {len(gbif_recs)} fetched -> {p} new, {d} duped")
            else:
                print(f"{prefix} | GBIF: 0 real records")
            time.sleep(0.4)

        if args.source in ("inat", "both"):
            inat_recs = fetch_inat_records(sp.scientific_name, limit=args.limit)
            inat_fetched += len(inat_recs)
            if inat_recs:
                p, d = persist_records(db, inat_recs, sp, inat_src, args.dry_run)
                inat_persisted += p; inat_duped += d; sp_total += p
                print(f"{prefix} | iNat: {len(inat_recs)} fetched -> {p} new, {d} duped")
            else:
                print(f"{prefix} | iNat: 0 real records")
            time.sleep(0.6)

        if sp_total > 0:
            species_with_obs.append(sp.scientific_name)
        elif not gbif_recs and not inat_recs:
            species_no_coords.append(sp.scientific_name)

    after_species = db.query(Species).count()
    after_obs = db.query(Observation).count()
    after_by_class = dict(db.query(Species.class_name, func.count(Species.id)).group_by(Species.class_name).all())
    obs_by_class = {}
    for cls in target_classes:
        sp_ids = [sp.id for sp in db.query(Species).filter(Species.class_name == cls).all()]
        obs_by_class[cls] = db.query(Observation.species_id).filter(Observation.species_id.in_(sp_ids)).distinct().count() if sp_ids else 0
    db.close()

    print(f"\n{'=' * 72}\n  FINAL EXPANSION REPORT\n{'=' * 72}")
    if args.dry_run:
        print("  *** DRY-RUN MODE - No data was written to the database ***\n")
    print(f"  BEFORE: Species={before_species}  Observations={before_obs}")
    print(f"  AFTER:  Species={after_species}  Observations={after_obs}")
    print(f"  NEW:    Species added={new_count}  Observations added={after_obs - before_obs}")
    print("\n  TAXONOMIC DISTRIBUTION (after):")
    for cls, cnt in sorted(after_by_class.items()):
        print(f"    {cls:15s}: {cnt:4d} species  ({obs_by_class.get(cls, '?')} with observations)")
    print(f"\n  OBSERVATION SOURCES:")
    print(f"    GBIF:        fetched={gbif_fetched}  persisted={gbif_persisted}  duped={gbif_duped}")
    print(f"    iNaturalist: fetched={inat_fetched}  persisted={inat_persisted}  duped={inat_duped}")
    print(f"\n  Species with geographic observations: {len(species_with_obs)}")
    for s in sorted(species_with_obs):
        print(f"    + {s}")
    if species_no_coords:
        print(f"\n  Species with no real-API coordinate data: {len(species_no_coords)}")
        for s in sorted(species_no_coords):
            print(f"    - {s}")
    print(f"\n{'=' * 72}")


if __name__ == "__main__":
    main()
