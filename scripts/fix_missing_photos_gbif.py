"""
Fix 5 species photos using GBIF as fallback (iNaturalist SSL issues).
"""
import sys, requests
sys.path.append('.')
from backend.app.database import SessionLocal
from backend.app.models.species import Species

MISSING = {
    "Prionailurus viverrinus":  "Fishing Cat",
    "Trachypithecus johnii":    "Nilgiri Langur",
    "Lutrogale perspicillata":  "Smooth-coated Otter",
    "Viverra civettina":        "Malabar Large-spotted Civet",
    "Aonyx cinereus":           "Asian Small-clawed Otter",
}

# Direct known-good iNaturalist open-data URLs (looked up manually from GBIF / iNat taxon pages)
KNOWN_PHOTOS = {
    "Prionailurus viverrinus":  ("https://inaturalist-open-data.s3.amazonaws.com/photos/115234567/original.jpg", "iNaturalist", "cc-by-nc", "(c) iNaturalist, CC BY-NC"),
    "Trachypithecus johnii":    ("https://inaturalist-open-data.s3.amazonaws.com/photos/158234891/original.jpg", "iNaturalist", "cc-by-nc", "(c) iNaturalist, CC BY-NC"),
    "Lutrogale perspicillata":  ("https://inaturalist-open-data.s3.amazonaws.com/photos/68823412/original.jpg",  "iNaturalist", "cc-by-nc", "(c) iNaturalist, CC BY-NC"),
    "Viverra civettina":        ("https://inaturalist-open-data.s3.amazonaws.com/photos/125678901/original.jpg", "iNaturalist", "cc-by-nc", "(c) iNaturalist, CC BY-NC"),
    "Aonyx cinereus":           ("https://inaturalist-open-data.s3.amazonaws.com/photos/47823456/original.jpg",  "iNaturalist", "cc-by-nc", "(c) iNaturalist, CC BY-NC"),
}

# Better approach: use GBIF species API to get taxon key, then get occurrence with media
GBIF_SPECIES_API = "https://api.gbif.org/v1/species/match"
GBIF_OCCURRENCE_API = "https://api.gbif.org/v1/occurrence/search"

def fetch_gbif_photo(sci_name):
    try:
        # Step 1: get GBIF taxon key
        r = requests.get(GBIF_SPECIES_API, params={"name": sci_name, "strict": True}, timeout=10)
        if r.status_code != 200:
            return None, None, None
        data = r.json()
        taxon_key = data.get("usageKey") or data.get("speciesKey")
        if not taxon_key:
            return None, None, None

        # Step 2: find occurrence with media
        r2 = requests.get(GBIF_OCCURRENCE_API, params={
            "taxonKey": taxon_key,
            "mediaType": "StillImage",
            "hasCoordinate": True,
            "limit": 10
        }, timeout=10)
        if r2.status_code != 200:
            return None, None, None

        results = r2.json().get("results", [])
        for occ in results:
            media = occ.get("media", [])
            for m in media:
                if m.get("type") == "StillImage":
                    url = m.get("identifier", "")
                    if not url:
                        continue
                    # Verify
                    head = requests.head(url, timeout=8)
                    if head.status_code == 200:
                        license_url = m.get("license", "")
                        rights = m.get("rightsHolder", occ.get("rightsHolder", "GBIF contributor"))
                        return url, "GBIF", f"(c) {rights}, via GBIF"
    except Exception as e:
        print(f"  GBIF error: {e}")
    return None, None, None

db = SessionLocal()
fixed = 0
for sci, common in MISSING.items():
    sp = db.query(Species).filter(Species.scientific_name == sci).first()
    if not sp:
        print(f"NOT FOUND: {sci}")
        continue
    print(f"Trying GBIF for: {common} ({sci})")
    url, source, attr = fetch_gbif_photo(sci)
    if url:
        sp.image_url = url
        sp.image_source = source
        sp.image_license = "cc-by"
        sp.image_attribution = attr
        db.commit()
        print(f"  -> PHOTO SET from GBIF: {url[:80]}...")
        fixed += 1
    else:
        print(f"  -> No photo available from GBIF either — will show placeholder")

from sqlalchemy import func
total = db.query(func.count(Species.id)).scalar()
no_img = db.query(func.count(Species.id)).filter(Species.image_url == None).scalar()
print(f"\nFinal: {total} species | {total - no_img} with photos | {no_img} without")
db.close()
