import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger("wildlife_platform.ingestion")
logging.basicConfig(level=logging.INFO)


class BaseIngestionClient(ABC):
    """
    Abstract base adapter for external biodiversity data sources.
    Provides standard session handling, rate-limiting, error trapping,
    provenance tracking, and fallback cache mechanisms.
    """

    def __init__(self, name: str, base_url: str, rate_limit_delay_seconds: float = 0.5):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.rate_limit_delay = rate_limit_delay_seconds
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "WildlifeConservationIntelligencePlatform/1.0 (Academic Research; contact@wildlife.ac.in)"
        })

    def _safe_get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """
        Executes an HTTP GET request with rate limiting and timeout safeguards.
        Returns parsed JSON or None if an error occurs.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            time.sleep(self.rate_limit_delay)
            req_headers = self.session.headers.copy()
            if headers:
                req_headers.update(headers)
            response = self.session.get(url, params=params, headers=req_headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"[{self.name}] API request to {url} failed: {e}. Utilizing fallback dataset if configured.")
            return None

    @abstractmethod
    def fetch_records(self, scientific_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch occurrence records for a specific taxon. Must return standardized observation dicts.
        """
        pass

    @abstractmethod
    def get_fallback_data(self, scientific_name: str) -> List[Dict[str, Any]]:
        """
        Provides academically defensible local mock records when API is unreachable or unauthenticated.
        """
        pass
