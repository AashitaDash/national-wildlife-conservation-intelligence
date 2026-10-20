import re
from typing import Dict, Any, List


class ThreatMatcher:
    """
    Threat extraction engine mapping linguistic cues to the IUCN Threat Classification Scheme.
    Associates detected threats with confidence multipliers and context spans.
    """

    THREAT_RULES = {
        "Poaching & Snaring": {
            "keywords": [
                r"\bpoach(?:ing|er|ers)?\b",
                r"\bsnare[s]?\b",
                r"\bwire snare[s]?\b",
                r"\bjaw trap[s]?\b",
                r"\billegal hunting\b",
                r"\billicit trade\b",
                r"\btusk[s]?\b",
                r"\brhino horn[s]?\b",
                r"\btiger pelt[s]?\b",
                r"\bpangolin scale[s]?\b"
            ],
            "severity_weight": 2.5
        },
        "Habitat Fragmentation & Encroachment": {
            "keywords": [
                r"\bfragmentation\b",
                r"\bencroachment\b",
                r"\bhabitat loss\b",
                r"\bsever(?:ed|ing)? corridor[s]?\b",
                r"\bmigratory route[s]? severed\b",
                r"\bcanopy clearance\b",
                r"\bforest division buffer\b"
            ],
            "severity_weight": 2.3
        },
        "Human-Wildlife Conflict": {
            "keywords": [
                r"\bhuman[- ]wildlife conflict\b",
                r"\bhuman[- ]elephant conflict\b",
                r"\bcrop raid(?:ing)?\b",
                r"\bpaddy destruction\b",
                r"\bretaliat(?:ory|ion)\b",
                r"\blivestock depredation\b",
                r"\bvulnerable village[s]?\b"
            ],
            "severity_weight": 2.0
        },
        "Linear Infrastructure & Collisions": {
            "keywords": [
                r"\brailway(?: line[s]?)?\b",
                r"\btrain collision[s]?\b",
                r"\bfreight train[s]?\b",
                r"\bhighway[s]?\b",
                r"\broad widening\b",
                r"\bvehicular collision[s]?\b",
                r"\belevated corridor[s]?\b"
            ],
            "severity_weight": 2.4
        },
        "Transmission Line Electrocution": {
            "keywords": [
                r"\belectrocution\b",
                r"\btransmission line[s]?\b",
                r"\boverhead power cable[s]?\b",
                r"\bpowerline[s]?\b",
                r"\b11\s?kv\b",
                r"\bsagging wire[s]?\b",
                r"\buninsulated\b"
            ],
            "severity_weight": 2.5
        },
        "Forest Fire & Canopy Burning": {
            "keywords": [
                r"\bforest fire[s]?\b",
                r"\bwildfire[s]?\b",
                r"\bcanopy burning\b",
                r"\bunderstory blaze\b"
            ],
            "severity_weight": 1.8
        },
        "Agricultural Expansion & Deforestation": {
            "keywords": [
                r"\bagricultural expansion\b",
                r"\bmonoculture\b",
                r"\bfringe agricultural zone[s]?\b",
                r"\bdeforestation\b",
                r"\bfarm plot[s]?\b"
            ],
            "severity_weight": 2.1
        },
        "Invasive Alien Flora": {
            "keywords": [
                r"\binvasive\b",
                r"\blantana\b",
                r"\bprosopis juliflora\b",
                r"\bsenna spectabilis\b",
                r"\bweed infestation\b"
            ],
            "severity_weight": 1.5
        },
        "Mining & Quarrying Disturbance": {
            "keywords": [
                r"\bmining\b",
                r"\bquarrying\b",
                r"\bopen[- ]cast\b",
                r"\biron ore\b",
                r"\bbauxite\b",
                r"\bsand mining\b"
            ],
            "severity_weight": 2.4
        },
        "Water Scarcity & Prolonged Drought": {
            "keywords": [
                r"\bdrought\b",
                r"\bwater scarcity\b",
                r"\bdried waterhole[s]?\b",
                r"\bmonsoon inundation\b"
            ],
            "severity_weight": 1.6
        }
    }

    @classmethod
    def extract_threats(cls, text: str) -> List[Dict[str, Any]]:
        """
        Analyzes text and returns structured threats with confidence score and evidence matches.
        """
        text_lower = text.lower()
        extracted = []

        for category, meta in cls.THREAT_RULES.items():
            matches_found = []
            for pattern in meta["keywords"]:
                found = re.findall(pattern, text_lower)
                if found:
                    matches_found.extend(found)

            if matches_found:
                # Calculate confidence based on occurrence frequency and term variety
                raw_count = len(matches_found)
                confidence = min(0.98, 0.65 + (raw_count * 0.08))

                extracted.append({
                    "category_name": category,
                    "severity_weight": meta["severity_weight"],
                    "confidence_score": round(confidence, 3),
                    "mention_count": raw_count,
                    "matched_snippets": list(set(matches_found))
                })

        # Sort descending by confidence * severity
        extracted.sort(key=lambda x: x["confidence_score"] * x["severity_weight"], reverse=True)
        return extracted


# Class alias for backward compatibility
ThreatKeywordMatcher = ThreatMatcher
