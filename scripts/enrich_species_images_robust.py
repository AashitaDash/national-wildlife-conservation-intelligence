import sys
import os
import time
import requests

# Add root to pythonpath
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import sessionmaker
from backend.app.database import engine
from backend.app.models.species import Species

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def fetch_inaturalist(sci_name):
    try:
        url = f"https://api.inaturalist.org/v1/taxa?q={sci_name}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            for r in results:
                # Exact match
                if r.get("name", "").lower() == sci_name.lower():
                    photo = r.get("default_photo")
                    if photo and photo.get("medium_url"):
                        img_url = photo.get("medium_url")
                        if "medium" in img_url:
                            img_url = img_url.replace("medium", "large")
                        return {
                            "url": img_url,
                            "source": "iNaturalist",
                            "license": photo.get("license_code"),
                            "attribution": photo.get("attribution")
                        }
    except Exception:
        pass
    return None

def fetch_gbif(sci_name):
    try:
        match_url = f"https://api.gbif.org/v1/species/match?name={sci_name}"
        match_resp = requests.get(match_url, timeout=10)
        if match_resp.status_code == 200:
            match_data = match_resp.json()
            if match_data.get("matchType") == "EXACT" and match_data.get("usageKey"):
                usage_key = match_data.get("usageKey")
                occ_url = f"https://api.gbif.org/v1/occurrence/search?taxonKey={usage_key}&mediaType=StillImage&limit=20"
                occ_resp = requests.get(occ_url, timeout=10)
                if occ_resp.status_code == 200:
                    results = occ_resp.json().get("results", [])
                    for occ in results:
                        if occ.get("species", "").lower() == sci_name.lower() or occ.get("scientificName", "").lower().startswith(sci_name.lower()):
                            for m in occ.get("media", []):
                                if m.get("type") == "StillImage" and m.get("identifier"):
                                    return {
                                        "url": m.get("identifier"),
                                        "source": "GBIF",
                                        "license": m.get("license") or m.get("rights"),
                                        "attribution": m.get("publisher") or m.get("rightsHolder")
                                    }
    except Exception:
        pass
    return None

def fetch_wikimedia(sci_name):
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&titles={sci_name}&format=json&pithumbsize=1000"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            pages = resp.json().get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if page_id != "-1" and "thumbnail" in page_data:
                    title = page_data.get("title", "")
                    if title.lower() == sci_name.lower():
                        return {
                            "url": page_data["thumbnail"]["source"],
                            "source": "Wikimedia Commons",
                            "license": "Public Domain / CC",
                            "attribution": "Wikimedia Commons"
                        }
    except Exception:
        pass
    return None

def main():
    db = SessionLocal()
    species_list = db.query(Species).order_by(Species.id).all()
    total = len(species_list)
    
    stats = {
        "iNaturalist": 0,
        "GBIF": 0,
        "Wikimedia Commons": 0,
        "None": 0
    }
    
    no_image_list = []
    
    for i, sp in enumerate(species_list):
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
            if img_data.get("license"):
                sp.image_license = str(img_data["license"])[:100]
            if img_data.get("attribution"):
                sp.image_attribution = str(img_data["attribution"])[:500]
            db.commit()
            print(f"[{i+1}/{total}] {sci_name} -> {img_data['source']} [OK]")
        else:
            sp.image_url = None
            sp.image_source = None
            sp.image_license = None
            sp.image_attribution = None
            db.commit()
            stats["None"] += 1
            no_image_list.append(sp)
            print(f"[{i+1}/{total}] {sci_name} -> No verified image found [FAIL]")
            
        time.sleep(0.5)
        
    print("\n========================================")
    print("SPECIES IMAGE ENRICHMENT REPORT")
    print("========================================")
    print(f"Total species: {total}")
    print()
    print(f"iNaturalist: {stats['iNaturalist']}")
    print(f"GBIF: {stats['GBIF']}")
    print(f"Wikimedia Commons: {stats['Wikimedia Commons']}")
    print()
    verified = stats["iNaturalist"] + stats["GBIF"] + stats["Wikimedia Commons"]
    print(f"Verified images: {verified}")
    print(f"No verified image: {stats['None']}")
    print()
    
    if no_image_list:
        print("For every species without an image, print:\nID | Common Name | Scientific Name | Reason")
        for sp in no_image_list:
            print(f"{sp.id} | {sp.common_name} | {sp.scientific_name} | No exact taxonomic match with valid photo found")

    print("========================================")

if __name__ == "__main__":
    main()
