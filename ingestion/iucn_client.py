"""
IUCN Red List API v4 Client
----------------------------
Uses the official IUCN Red List API v4 endpoint.
Authentication: Bearer token (from IUCN_API_TOKEN env var).

The v4 API /taxa/scientific_name endpoint returns:
  - IUCN SIS taxon ID
  - Authoritative scientific name
  - Full taxonomy (kingdom/phylum/class/order/family/genus)
  - Common names (all languages)
  - Synonyms
  - SSC Group metadata

Red List category is stored in the existing species master (iucn_category column).
This client enriches species with IUCN identifiers and authoritative taxonomy.
"""

import datetime
import logging
import time
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger("wildlife_platform.ingestion.iucn")


class IUCNClient:
    BASE_URL = "https://api.iucnredlist.org/api/v4"
    RATE_LIMIT_DELAY = 2.0  # seconds between requests (be conservative)

    def __init__(self, token: Optional[str] = None):
        from backend.app.config import settings
        self.token = token or settings.IUCN_API_TOKEN or settings.IUCN_API_KEY or ""
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "WildlifeConservationPlatform/1.0 (Academic; contact@wildlife.ac.in)",
            "Accept": "application/json",
        })
        self._configured = bool(self.token) and not self.token.startswith("mock")

    def is_configured(self) -> bool:
        return self._configured

    def fetch_taxon(self, genus_name: str, species_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch IUCN v4 taxon record by genus + species name.
        Returns normalized dict or None on failure.
        """
        if not self._configured:
            logger.warning("[IUCN] Token not configured, skipping.")
            return None

        time.sleep(self.RATE_LIMIT_DELAY)
        try:
            r = self.session.get(
                f"{self.BASE_URL}/taxa/scientific_name",
                params={"genus_name": genus_name, "species_name": species_name},
                timeout=20,
            )
            if r.status_code == 200:
                data = r.json()
                return self._normalize(data.get("taxon", {}), genus_name, species_name)
            elif r.status_code == 404:
                logger.info(f"[IUCN] No taxon found for {genus_name} {species_name}")
                return None
            else:
                logger.warning(f"[IUCN] {r.status_code} for {genus_name} {species_name}: {r.text[:200]}")
                return None
        except requests.RequestException as e:
            logger.error(f"[IUCN] Request failed for {genus_name} {species_name}: {e}")
            return None

    def _normalize(self, taxon: Dict, genus_name: str, species_name: str) -> Dict[str, Any]:
        """Normalize IUCN v4 taxon response to our schema."""
        common_names = taxon.get("common_names", [])
        main_common = next((c["name"] for c in common_names if c.get("main")), None)
        all_common_en = [c["name"] for c in common_names if c.get("language") == "eng"]

        synonyms = [s.get("name") for s in taxon.get("synonyms", []) if s.get("name")]

        return {
            "sis_id": taxon.get("sis_id"),
            "scientific_name": taxon.get("scientific_name", f"{genus_name} {species_name}"),
            "genus_name": taxon.get("genus_name", genus_name),
            "species_name": taxon.get("species_name", species_name),
            "authority": taxon.get("authority"),
            "kingdom_name": taxon.get("kingdom_name"),
            "phylum_name": taxon.get("phylum_name"),
            "class_name": taxon.get("class_name"),
            "order_name": taxon.get("order_name"),
            "family_name": taxon.get("family_name"),
            "main_common_name": main_common,
            "common_names_en": all_common_en,
            "synonyms": synonyms,
            "ssc_groups": [g.get("name") for g in taxon.get("ssc_groups", [])],
            "source": "IUCN",
            "source_url": f"https://www.iucnredlist.org/species/{taxon.get('sis_id', '')}",
            "retrieved_at": datetime.datetime.utcnow().isoformat(),
            "raw_response": taxon,
        }
