import os, sys, requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.config import settings

token = settings.IUCN_API_TOKEN or settings.IUCN_API_KEY or ""
print(f"Token length: {len(token)}, starts: {token[:6]}...")

base = "https://api.iucnredlist.org/api/v4"

# Try different auth header formats
tests = [
    ("Bearer token", {"Authorization": f"Bearer {token}"}),
    ("Token token",  {"Authorization": f"Token {token}"}),
    ("Raw header",   {"Authorization": token}),
    ("x-api-key",    {"x-api-key": token}),
]

endpoints = [
    "/taxa/scientific_name?name=Panthera+tigris",
    "/species/Panthera+tigris/assessments",
    "/species",
]

print("\n--- Testing auth header formats on /taxa/scientific_name ---")
for name, headers in tests:
    try:
        r = requests.get(
            f"{base}/taxa/scientific_name",
            params={"name": "Panthera tigris"},
            headers=headers,
            timeout=15
        )
        print(f"  [{name}]: {r.status_code} - {r.text[:100]}")
    except Exception as e:
        print(f"  [{name}]: Exception {e}")

print("\n--- Testing endpoints ---")
for ep in endpoints:
    try:
        r = requests.get(
            f"{base}{ep}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        print(f"  {ep}: {r.status_code} - {r.text[:150]}")
    except Exception as e:
        print(f"  {ep}: Exception {e}")

# Also try the v3 API which is documented at a different place
print("\n--- Trying IUCN v3 API (apiv3) ---")
try:
    r = requests.get(
        "https://apiv3.iucnredlist.org/api/v3/species/Panthera tigris",
        params={"token": token},
        timeout=15
    )
    print(f"  v3/species: {r.status_code} - {r.text[:200]}")
except Exception as e:
    print(f"  v3/species: Exception {e}")

try:
    r = requests.get(
        "https://apiv3.iucnredlist.org/api/v3/species/Panthera%20tigris",
        params={"token": token},
        timeout=15
    )
    print(f"  v3/species (encoded): {r.status_code} - {r.text[:200]}")
except Exception as e:
    print(f"  v3 encoded: Exception {e}")
