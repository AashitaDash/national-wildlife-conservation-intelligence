import os, sys, requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.config import settings

print("=== API KEY STATUS ===")
ebird_key = settings.EBIRD_API_KEY or ""
iucn_token = settings.IUCN_API_TOKEN or settings.IUCN_API_KEY or ""
print(f"  EBIRD_API_KEY : {'CONFIGURED' if ebird_key and not ebird_key.startswith('mock') else 'MISSING'}")
print(f"  IUCN_API_TOKEN: {'CONFIGURED' if iucn_token and not iucn_token.startswith('mock') else 'MISSING'}")
print()

# --- eBird test ---
print("[TEST 1/4] eBird API - Recent notable observations in India...")
try:
    resp = requests.get(
        "https://api.ebird.org/v2/data/obs/IN/recent/notable",
        params={"maxResults": 5},
        headers={"X-eBirdApiToken": ebird_key},
        timeout=15
    )
    print(f"  HTTP Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  Records returned: {len(data)}")
        if data:
            item = data[0]
            name = item.get("comName", "?")
            sci = item.get("sciName", "?")
            loc = item.get("locName", "?")
            print(f"  Sample record: {name} ({sci}) @ {loc}")
    else:
        print(f"  Error: {resp.text[:300]}")
except Exception as e:
    print(f"  Exception: {e}")

print()

# --- eBird regional test ---
print("[TEST 2/4] eBird API - Recent obs (all species) in India, last 7 days...")
try:
    resp2 = requests.get(
        "https://api.ebird.org/v2/data/obs/IN/recent",
        params={"maxResults": 5, "back": 7},
        headers={"X-eBirdApiToken": ebird_key},
        timeout=15
    )
    print(f"  HTTP Status: {resp2.status_code}")
    if resp2.status_code == 200:
        data2 = resp2.json()
        print(f"  Records returned: {len(data2)}")
        if data2:
            item = data2[0]
            print(f"  Sample: {item.get('comName')} ({item.get('sciName')}) @ {item.get('locName')}")
    else:
        print(f"  Error: {resp2.text[:300]}")
except Exception as e:
    print(f"  Exception: {e}")

print()

# --- IUCN v4 test ---
print("[TEST 3/4] IUCN Red List API v4 - Assess Panthera tigris...")
try:
    resp3 = requests.get(
        "https://api.iucnredlist.org/api/v4/taxa/scientific_name",
        params={"name": "Panthera tigris"},
        headers={"Authorization": f"Token {iucn_token}"},
        timeout=20
    )
    print(f"  HTTP Status: {resp3.status_code}")
    if resp3.status_code == 200:
        data3 = resp3.json()
        print(f"  Response type: {type(data3).__name__}")
        if isinstance(data3, dict):
            print(f"  Keys: {list(data3.keys())}")
            # Show first taxon if available
            for k in ["taxa", "result", "results", "assessments"]:
                if k in data3:
                    items = data3[k]
                    if items:
                        first = items[0] if isinstance(items, list) else items
                        print(f"  First [{k}]: {str(first)[:300]}")
                    break
        elif isinstance(data3, list) and data3:
            print(f"  First item: {str(data3[0])[:300]}")
    else:
        print(f"  Error: {resp3.text[:400]}")
except Exception as e:
    print(f"  Exception: {e}")

print()

# --- IUCN species list test ---
print("[TEST 4/4] IUCN Red List API v4 - Try species assessment endpoint...")
try:
    resp4 = requests.get(
        "https://api.iucnredlist.org/api/v4/species/Panthera_tigris",
        headers={"Authorization": f"Token {iucn_token}"},
        timeout=20
    )
    print(f"  HTTP Status: {resp4.status_code}")
    print(f"  Response: {resp4.text[:400]}")
except Exception as e:
    print(f"  Exception: {e}")

print()
print("=== API TESTS COMPLETE ===")
