import os, sys, requests, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.config import settings

token = settings.IUCN_API_TOKEN or settings.IUCN_API_KEY or ""
headers = {"Authorization": f"Bearer {token}"}
base = "https://api.iucnredlist.org/api/v4"

# Get the full taxon response to understand what conservation data is available
r = requests.get(
    f"{base}/taxa/scientific_name",
    params={"genus_name": "Panthera", "species_name": "tigris"},
    headers=headers, timeout=20
)
data = r.json()
taxon = data.get("taxon", {})
print("=== All taxon fields ===")
for k, v in taxon.items():
    if isinstance(v, list):
        print(f"  {k}: [{len(v)} items] {str(v[:2])[:100]}")
    else:
        print(f"  {k}: {v}")

# Check if there are assessment details embedded
print("\n=== Checking for red_list_category / assessment in taxon ===")
for key in ["red_list_category", "category", "assessment", "assessments", "red_list", "conservation_status", "iucn_category"]:
    if key in taxon:
        print(f"  {key}: {taxon[key]}")
    else:
        print(f"  {key}: NOT FOUND")
