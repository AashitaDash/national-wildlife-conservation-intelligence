import re
import datetime
from typing import Dict, Any, List, Optional, Tuple

# Bounding box for Indian Subcontinent & adjacent marine EEZ
INDIA_GEO_BOUNDS = {
    "min_lat": 6.0,
    "max_lat": 38.0,
    "min_lon": 68.0,
    "max_lon": 98.0
}


class DataCleaner:
    """
    Validation, coordinate sanitization, and deduplication utility
    for biodiversity observations across heterogeneous APIs.
    """

    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> Tuple[bool, str]:
        """
        Ensures latitude and longitude are valid decimal degrees
        and fall within the geographic bounding envelope.
        """
        if not (-90.0 <= lat <= 90.0):
            return False, f"Latitude {lat} out of valid bounds [-90, 90]"
        if not (-180.0 <= lon <= 180.0):
            return False, f"Longitude {lon} out of valid bounds [-180, 180]"

        # Verify within project regional envelope
        in_region = (
            INDIA_GEO_BOUNDS["min_lat"] <= lat <= INDIA_GEO_BOUNDS["max_lat"] and
            INDIA_GEO_BOUNDS["min_lon"] <= lon <= INDIA_GEO_BOUNDS["max_lon"]
        )
        if not in_region:
            return False, f"Coordinates ({lat}, {lon}) fall outside the Indian geographic envelope"

        return True, "Valid"

    @staticmethod
    def deduplicate_observations(observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filters duplicates within a batch based on:
        Species Name + 3-decimal (~110m) coordinate grid + observation date.
        """
        seen_keys = set()
        unique_records = []

        for obs in observations:
            try:
                sci_name = obs.get("scientific_name", "").strip().lower()
                lat = round(float(obs.get("latitude", 0)), 3)
                lon = round(float(obs.get("longitude", 0)), 3)
                obs_dt = obs.get("observed_at")
                date_key = obs_dt.strftime("%Y-%m-%d") if isinstance(obs_dt, datetime.datetime) else str(obs_dt)[:10]

                dedup_key = (sci_name, lat, lon, date_key)
                if dedup_key in seen_keys:
                    continue

                seen_keys.add(dedup_key)
                unique_records.append(obs)
            except Exception:
                continue

        return unique_records

    @staticmethod
    def canonicalize_species_name(name: str) -> str:
        """
        Strips taxonomic abbreviations (subsp., var.), whitespace, and capitalizes binomial name.
        """
        if not name:
            return ""
        # Remove common taxonomic notes
        cleaned = re.sub(r"\b(subsp\.|var\.|cf\.|aff\.|sp\.)\b.*", "", name, flags=re.IGNORECASE)
        parts = cleaned.strip().split()
        if len(parts) >= 2:
            return f"{parts[0].capitalize()} {parts[1].lower()}"
        elif len(parts) == 1:
            return parts[0].capitalize()
        return name.strip()


# Service alias for backward compatibility
DataCleanerService = DataCleaner
