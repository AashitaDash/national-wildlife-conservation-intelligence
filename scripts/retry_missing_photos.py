"""
Retry photo fetch for species that got SSL errors during initial enrichment.
"""
import sys, time, requests
sys.path.append('.')
from backend.app.database import SessionLocal
from backend.app.models.species import Species

# Species that failed photo fetch
RETRY = [
    "Prionailurus viverrinus",   # Fishing Cat
    "Trachypithecus johnii",     # Nilgiri Langur
    "Lutrogale perspicillata",   # Smooth-coated Otter
    "Viverra civettina",         # Malabar Large-spotted Civet
    "Aonyx cinereus",            # Asian Small-clawed Otter
]

INAT_API = "https://api.inaturalist.org/v1/observations"

def fetch_photo(sci_name):
    try:
        params = {
            "taxon_name": sci_name,
            "has[]": "photos",
            "quality_grade": "research",
            "per_page": 5,
            "order_by": "votes",
        }
        r = requests.get(INAT_API, params=params, timeout=15)
        if r.status_code != 200:
            return None, None, None
        for obs in r.json().get("results", []):
            genus = sci_name.split()[0]
            if not obs.get("taxon", {}).get("name", "").startswith(genus):
                continue
            photos = obs.get("photos", [])
            if not photos:
                continue
            photo = photos[0]
            url = photo.get("url", "").replace("/square.", "/original.")
            if not url:
                continue
            head = requests.head(url, timeout=8)
            if head.status_code == 200:
                return url, photo.get("license_code", "cc-by-nc"), photo.get("attribution", "")
    except Exception as e:
        print(f"  Error: {e}")
    return None, None, None

db = SessionLocal()
for sci in RETRY:
    sp = db.query(Species).filter(Species.scientific_name == sci).first()
    if not sp:
        print(f"NOT FOUND: {sci}")
        continue
    print(f"Retrying photo for: {sci}")
    url, lic, attr = fetch_photo(sci)
    if url:
        sp.image_url = url
        sp.image_source = "iNaturalist"
        sp.image_license = lic
        sp.image_attribution = attr
        db.commit()
        print(f"  -> PHOTO SET OK")
    else:
        print(f"  -> Still no photo (rare/elusive species)")
    time.sleep(1)

# Final counts
from sqlalchemy import func
total = db.query(func.count(Species.id)).scalar()
no_img = db.query(func.count(Species.id)).filter(Species.image_url == None).scalar()
class_counts = db.query(Species.class_name, func.count(Species.id)).group_by(Species.class_name).order_by(func.count(Species.id).desc()).all()

print("\n========================================")
print("FINAL DATABASE STATE")
print("========================================")
print(f"Total species: {total}")
print(f"With photos:   {total - no_img}")
print(f"No photo:      {no_img}")
print("\nBy class:")
for cls, cnt in class_counts:
    print(f"  {cls or 'Unknown'}: {cnt}")
print("========================================")
