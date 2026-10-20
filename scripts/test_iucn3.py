import os, sys, requests, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.config import settings

token = settings.IUCN_API_TOKEN or settings.IUCN_API_KEY or ""
headers = {"Authorization": f"Bearer {token}"}
base = "https://api.iucnredlist.org/api/v4"

print("=== IUCN v4 Full Taxon Response (Panthera tigris) ===")
r = requests.get(
    f"{base}/taxa/scientific_name",
    params={"genus_name": "Panthera", "species_name": "tigris"},
    headers=headers, timeout=20
)
data = r.json()
print(json.dumps(data, indent=2)[:3000])

print("\n\n=== Trying assessment endpoints with sis_id ===")
sis_id = data.get("taxon", {}).get("sis_id", 15955)
print(f"SIS ID: {sis_id}")

for ep in [
    f"/taxa/{sis_id}/assessments",
    f"/assessments/{sis_id}",
    f"/taxa/{sis_id}",
]:
    r2 = requests.get(f"{base}{ep}", headers=headers, timeout=15)
    print(f"\n  {ep}: {r2.status_code}")
    print(f"  {r2.text[:300]}")
