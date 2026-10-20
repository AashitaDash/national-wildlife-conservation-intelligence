"""
eBird API 2.0 Client
---------------------
Official Cornell Lab of Ornithology eBird API.
Auth: X-eBirdApiToken header (EBIRD_API_KEY env var).

Endpoints used:
  - /data/obs/{regionCode}/recent         - recent observations in a region
  - /data/obs/{regionCode}/recent/notable - notable (rare) observations
  - /data/obs/geo/recent                  - recent obs near a point

India region codes: IN (national), IN-OD (Odisha), IN-RJ (Rajasthan), etc.
"""

import datetime
import logging
import time
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger("wildlife_platform.ingestion.ebird")

# Indian state eBird region codes (focus on areas with target species)
INDIA_REGIONS = ["IN-OD", "IN-RJ", "IN-KA", "IN-TN", "IN-MH", "IN-WB", "IN-JH", "IN-HP"]


class EBirdV2Client:
    BASE_URL = "https://api.ebird.org/v2"
    RATE_LIMIT_DELAY = 0.5

    def __init__(self, api_key: Optional[str] = None):
        from backend.app.config import settings
        self.api_key = api_key or settings.EBIRD_API_KEY or ""
        self.session = requests.Session()
        self.session.headers.update({
            "X-eBirdApiToken": self.api_key,
            "User-Agent": "WildlifeConservationPlatform/1.0 (Academic; contact@wildlife.ac.in)",
        })
        self._configured = bool(self.api_key) and not self.api_key.startswith("mock")

    def is_configured(self) -> bool:
        return self._configured

    def _get(self, endpoint: str, params: Optional[dict] = None) -> Optional[Any]:
        time.sleep(self.RATE_LIMIT_DELAY)
        try:
            r = self.session.get(f"{self.BASE_URL}/{endpoint}", params=params, timeout=15)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            logger.warning(f"[eBird] Request failed {endpoint}: {e}")
            return None

    def fetch_recent_notable(self, region_code: str = "IN", max_results: int = 100, back_days: int = 14) -> List[Dict]:
        """Fetch recent notable observations in a region."""
        data = self._get(
            f"data/obs/{region_code}/recent/notable",
            params={"maxResults": max_results, "back": back_days, "detail": "full"}
        )
        if not data or not isinstance(data, list):
            return []
        return [self._normalize(item, region_code) for item in data if self._has_coords(item)]

    def fetch_recent_obs(self, region_code: str = "IN", max_results: int = 100, back_days: int = 7) -> List[Dict]:
        """Fetch recent all-species observations in a region."""
        data = self._get(
            f"data/obs/{region_code}/recent",
            params={"maxResults": max_results, "back": back_days}
        )
        if not data or not isinstance(data, list):
            return []
        return [self._normalize(item, region_code) for item in data if self._has_coords(item)]

    def fetch_species_obs(self, scientific_name: str, region_code: str = "IN", back_days: int = 30) -> List[Dict]:
        """Fetch recent obs for a specific species in a region using species code lookup."""
        # eBird uses species codes; we search recent notable and filter by sciName
        data = self._get(
            f"data/obs/{region_code}/recent/notable",
            params={"maxResults": 200, "back": back_days, "detail": "full"}
        )
        if not data or not isinstance(data, list):
            return []
        matching = [item for item in data if scientific_name.lower() in item.get("sciName", "").lower()]
        return [self._normalize(item, region_code) for item in matching if self._has_coords(item)]

    def _has_coords(self, item: dict) -> bool:
        return item.get("lat") is not None and item.get("lng") is not None

    def _normalize(self, item: dict, region_code: str) -> Dict[str, Any]:
        obs_date_str = item.get("obsDt", "")
        try:
            if " " in obs_date_str:
                obs_dt = datetime.datetime.strptime(obs_date_str, "%Y-%m-%d %H:%M")
            else:
                obs_dt = datetime.datetime.strptime(obs_date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            obs_dt = datetime.datetime.utcnow()

        return {
            "source": "eBird",
            "scientific_name": item.get("sciName", ""),
            "common_name": item.get("comName", ""),
            "latitude": float(item.get("lat", 0)),
            "longitude": float(item.get("lng", 0)),
            "accuracy_meters": 100.0,
            "observed_at": obs_dt,
            "verification_status": "VERIFIED" if item.get("obsValid") else "CITIZEN_PENDING",
            "notes": (
                f"eBird {region_code}: {item.get('comName')} at {item.get('locName', 'India')}. "
                f"Count: {item.get('howMany', 'X')}. "
                f"Checklist: {item.get('subId', 'N/A')}"
            ),
            "raw_metadata": {
                "ebird_subId": item.get("subId"),
                "ebird_locId": item.get("locId"),
                "ebird_locName": item.get("locName"),
                "ebird_obsValid": item.get("obsValid"),
                "ebird_obsReviewed": item.get("obsReviewed"),
                "ebird_howMany": item.get("howMany"),
                "ebird_region": region_code,
                "source_url": f"https://ebird.org/checklist/{item.get('subId', '')}",
                "retrieved_at": datetime.datetime.utcnow().isoformat(),
                "attribution": "Data provided by eBird (https://ebird.org), Cornell Lab of Ornithology",
            }
        }
