import os
import re
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger("wildlife_platform.nlp.ner")


class EntityExtractor:
    """
    Hybrid Named Entity Recognition (NER) system for wildlife conservation intelligence.
    Combines domain-specific gazetteers (species taxonomy, protected area boundaries)
    with pattern-based extraction for organizations, dates, and administrative jurisdictions.
    """

    def __init__(self, gazetteers_dir: str = None):
        if not gazetteers_dir:
            gazetteers_dir = os.path.join(os.path.dirname(__file__), "gazetteers")
        
        self.species_catalog = self._load_json(os.path.join(gazetteers_dir, "species_list.json"))
        self.locations_catalog = self._load_json(os.path.join(gazetteers_dir, "locations_list.json"))

        # Precompile organization regex patterns
        self.org_patterns = [
            r"\b(?:Forest Department|Forest Division|State Forest Service)\b",
            r"\b(?:Wildlife Institute of India|WII|Wildlife Trust of India|WTI)\b",
            r"\b(?:World Wide Fund for Nature|WWF|WWF[- ]India)\b",
            r"\b(?:Bombay Natural History Society|BNHS)\b",
            r"\b(?:National Tiger Conservation Authority|NTCA)\b",
            r"\b(?:Rapid Response Team|Anti-Poaching Camp|Eco-Development Committee)\b"
        ]

        # Temporal patterns
        self.date_patterns = [
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
            r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b",
            r"\b(?:monsoon|winter|summer|post-monsoon)\s+\d{4}\b",
            r"\b(?:past|last)\s+(?:\d+|two|three|four|five|six|eighteen)\s+(?:days|weeks|months|years)\b"
        ]

    def _load_json(self, filepath: str) -> List[Dict[str, Any]]:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load gazetteer from {filepath}: {e}")
            return []

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Executes hybrid NER across species, locations, organizations, and temporal terms.
        """
        text_lower = text.lower()

        # 1. Species extraction
        extracted_species = []
        for sp in self.species_catalog:
            match_count = 0
            matched_terms = set()
            for synonym in sp.get("synonyms", []):
                # Word boundary regex search
                pattern = rf"\b{re.escape(synonym)}\b"
                matches = re.findall(pattern, text_lower)
                if matches:
                    match_count += len(matches)
                    matched_terms.add(synonym)

            if match_count > 0:
                extracted_species.append({
                    "canonical_name": sp["canonical_name"],
                    "scientific_name": sp["scientific_name"],
                    "mention_count": match_count,
                    "matched_tokens": list(matched_terms)
                })

        # 2. Location extraction
        extracted_locations = []
        for loc in self.locations_catalog:
            match_count = 0
            matched_terms = set()
            for synonym in loc.get("synonyms", []):
                pattern = rf"\b{re.escape(synonym)}\b"
                matches = re.findall(pattern, text_lower)
                if matches:
                    match_count += len(matches)
                    matched_terms.add(synonym)

            if match_count > 0:
                extracted_locations.append({
                    "canonical_name": loc["canonical_name"],
                    "state": loc.get("state"),
                    "district": loc.get("district"),
                    "mention_count": match_count,
                    "matched_tokens": list(matched_terms)
                })

        # 3. Organization extraction
        extracted_orgs = set()
        for p in self.org_patterns:
            found = re.findall(p, text, flags=re.IGNORECASE)
            for item in found:
                extracted_orgs.add(item.strip())

        # 4. Temporal expression extraction
        extracted_dates = set()
        for p in self.date_patterns:
            found = re.findall(p, text, flags=re.IGNORECASE)
            for item in found:
                extracted_dates.add(item.strip())

        return {
            "species": extracted_species,
            "locations": extracted_locations,
            "organizations": sorted(list(extracted_orgs)),
            "temporal_expressions": sorted(list(extracted_dates))
        }


# Class alias for backward compatibility
GazetteerEntityExtractor = EntityExtractor
