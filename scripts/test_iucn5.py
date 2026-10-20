import os, sys, requests, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.config import settings

token = settings.IUCN_API_TOKEN or settings.IUCN_API_KEY or ""
headers = {"Authorization": f"Bearer {token}"}
base = "https://api.iucnredlist.org/api/v4"

# The taxon endpoint gives us the SIS ID. Now we need to get assessments.
# Try the correct assessment endpoint pattern for v4
sis_id = 15955  # Panthera tigris

endpoints_to_try = [
    f"/assessments?sis_id={sis_id}",
    f"/assessments?sis_taxon_id={sis_id}",
    f"/assessments?taxon_id={sis_id}",
    "/assessments?genus_name=Panthera&species_name=tigris",
    "/red_list_assessments?genus_name=Panthera&species_name=tigris",
    "/assessments/latest?genus_name=Panthera&species_name=tigris",
]

for ep in endpoints_to_try:
    r = requests.get(f"{base}{ep}", headers=headers, timeout=15)
    txt = r.text[:200]
    print(f"\n  {ep}")
    print(f"  Status: {r.status_code}")
    print(f"  Response: {txt}")
