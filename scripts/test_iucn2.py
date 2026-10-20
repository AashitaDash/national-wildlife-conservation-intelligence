import os, sys, requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.config import settings

token = settings.IUCN_API_TOKEN or settings.IUCN_API_KEY or ""
headers = {"Authorization": f"Bearer {token}"}
base = "https://api.iucnredlist.org/api/v4"

print("=== IUCN v4 API Endpoint Discovery ===\n")

# The v4 API uses genus_name + species_name separately
tests = [
    # Correct genus+species split
    ("taxa with genus+species", f"{base}/taxa/scientific_name", {"genus_name": "Panthera", "species_name": "tigris"}),
    ("taxa no params", f"{base}/taxa", {}),
    ("assessments for taxon", f"{base}/taxa/scientific_name/assessments", {"genus_name": "Panthera", "species_name": "tigris"}),
    ("website species", f"{base}/website/species", {"genus_name": "Panthera", "species_name": "tigris"}),
    ("species search", f"{base}/species/search", {"query": "Panthera tigris"}),
]

for name, url, params in tests:
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"[{name}]")
        print(f"  URL: {r.url}")
        print(f"  Status: {r.status_code}")
        txt = r.text[:300]
        print(f"  Response: {txt}")
        print()
    except Exception as e:
        print(f"[{name}] Exception: {e}\n")
