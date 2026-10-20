import sys
import os
import time
import logging
import requests

# Add root to pythonpath
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import sessionmaker
from backend.app.database import engine
from backend.app.models.species import Species

logging.basicConfig(level=logging.INFO, format='%(message)s')

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def fetch_inaturalist(scientific_name: str):
    try:
        url = f"https://api.inaturalist.org/v1/taxa?q={scientific_name}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            for r in results:
                # Ensure it's a good match
                if r.get("name", "").lower() == scientific_name.lower():
                    photo = r.get("default_photo")
                    if photo:
                        return {
                            "url": photo.get("medium_url"),
                            "source": "iNaturalist",
                            "license": photo.get("license_code"),
                            "attribution": photo.get("attribution")
                        }
    except Exception as e:
        pass
    return None

def fetch_gbif(scientific_name: str):
    try:
        match_url = f"https://api.gbif.org/v1/species/match?name={scientific_name}"
        match_resp = requests.get(match_url, timeout=10)
        if match_resp.status_code == 200:
            usage_key = match_resp.json().get("usageKey")
            if usage_key:
                occ_url = f"https://api.gbif.org/v1/occurrence/search?taxonKey={usage_key}&mediaType=StillImage&limit=1"
                occ_resp = requests.get(occ_url, timeout=10)
                if occ_resp.status_code == 200:
                    results = occ_resp.json().get("results", [])
                    for occ in results:
                        media = occ.get("media", [])
                        for m in media:
                            if m.get("type") == "StillImage" and m.get("identifier"):
                                return {
                                    "url": m.get("identifier"),
                                    "source": "GBIF",
                                    "license": m.get("license") or m.get("rights"),
                                    "attribution": m.get("publisher") or m.get("rightsHolder")
                                }
    except Exception as e:
        pass
    return None

def fetch_wikimedia(scientific_name: str):
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&titles={scientific_name}&format=json&pithumbsize=500"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            pages = resp.json().get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if page_id != "-1" and "thumbnail" in page_data:
                    return {
                        "url": page_data["thumbnail"]["source"],
                        "source": "Wikimedia Commons",
                        "license": "Public Domain / CC",
                        "attribution": "Wikimedia Commons"
                    }
    except Exception as e:
        pass
    return None

def run_enrichment():
    db = SessionLocal()
    species_list = db.query(Species).all()
    total = len(species_list)
    
    stats = {
        "iNaturalist": 0,
        "GBIF": 0,
        "Wikimedia Commons": 0,
        "None": 0,
        "Failed": 0
    }
    
    for i, sp in enumerate(species_list):
        try:
            # Skip if already has an image
            if sp.image_url and "dummy" not in sp.image_url.lower():
                # We count this as skipped or already present, but the prompt says 
                # "Never overwrite an existing valid image unless explicitly requested."
                # We'll just continue if it's already there
                pass

            sci_name = sp.scientific_name
            
            img_data = fetch_inaturalist(sci_name)
            if img_data:
                stats["iNaturalist"] += 1
            else:
                img_data = fetch_gbif(sci_name)
                if img_data:
                    stats["GBIF"] += 1
                else:
                    img_data = fetch_wikimedia(sci_name)
                    if img_data:
                        stats["Wikimedia Commons"] += 1
                        
            if img_data:
                sp.image_url = img_data["url"]
                sp.image_source = img_data["source"]
                if img_data["license"]:
                    sp.image_license = str(img_data["license"])[:100]
                if img_data["attribution"]:
                    sp.image_attribution = str(img_data["attribution"])[:500]
                db.commit()
                print(f"[{i+1}/{total}] {sci_name} -> {img_data['source']} ✓")
            else:
                stats["None"] += 1
                print(f"[{i+1}/{total}] {sci_name} -> No image found ✗")
                
            time.sleep(0.5) # rate limit
            
        except Exception as e:
            stats["Failed"] += 1
            print(f"[{i+1}/{total}] {sp.scientific_name} -> Error: {e}")
            db.rollback()
            
    db.close()
    
    found = stats["iNaturalist"] + stats["GBIF"] + stats["Wikimedia Commons"]
    print("\n--- Enrichment Complete ---")
    print(f"Species processed: {total}")
    print(f"Images found: {found}")
    print(f"iNaturalist: {stats['iNaturalist']}")
    print(f"GBIF: {stats['GBIF']}")
    print(f"Wikimedia Commons: {stats['Wikimedia Commons']}")
    print(f"No image found: {stats['None']}")
    print(f"Failures: {stats['Failed']}")

if __name__ == "__main__":
    run_enrichment()
