import datetime
from typing import Dict, Any, List
import pandas as pd
import numpy as np


class FeatureEngineeringService:
    """
    Extracts and constructs tabular spatio-temporal and NLP-derived feature matrices
    for species and regional conservation assessments.
    """

    IUCN_ORDINAL_MAP = {
        "LC": 1.0,  # Least Concern
        "NT": 2.0,  # Near Threatened
        "VU": 3.0,  # Vulnerable
        "EN": 4.0,  # Endangered
        "CR": 5.0,  # Critically Endangered
        "EW": 5.0,  # Extinct in the Wild
        "EX": 5.0,  # Extinct
        "DD": 2.5   # Data Deficient (assigned moderate baseline uncertainty)
    }

    @classmethod
    def compute_features_for_species_region(
        cls,
        species_id: int,
        iucn_category: str,
        observations: List[Dict[str, Any]],
        document_threats: List[Dict[str, Any]],
        current_time: datetime.datetime = None
    ) -> Dict[str, float]:
        """
        Constructs a structured feature dictionary for a species within a region.
        
        Features:
          1. obs_count_recent_14d: Total observations in the last 14 days
          2. obs_count_baseline_90d: Total observations in the last 90 days
          3. obs_temporal_trend: Normalized rate of change between 14d rate and 90d baseline
          4. threat_mention_count_30d: Count of NLP threat associations in past 30 days
          5. hwc_incident_ratio: Proportion of threats related to Human-Wildlife Conflict
          6. spatial_dispersion_std: Standard deviation of observation coordinates (geographic clustering)
          7. iucn_base_vulnerability: Ordinal score (1.0 to 5.0) from master IUCN 3.1 category
        """
        now = current_time or datetime.datetime.now(datetime.timezone.utc)
        dt_14d = now - datetime.timedelta(days=14)
        dt_30d = now - datetime.timedelta(days=30)
        dt_90d = now - datetime.timedelta(days=90)

        # 1. Temporal observation frequencies
        obs_14d = 0
        obs_90d = 0
        lats = []
        lons = []

        for obs in observations:
            obs_dt = obs.get("observed_at")
            if not obs_dt:
                continue
            if isinstance(obs_dt, str):
                try:
                    obs_dt = datetime.datetime.fromisoformat(obs_dt.replace("Z", "+00:00"))
                except Exception:
                    continue

            # Ensure timezone-aware comparison
            if obs_dt.tzinfo is None:
                obs_dt = obs_dt.replace(tzinfo=datetime.timezone.utc)

            if obs_dt >= dt_14d:
                obs_14d += 1
            if obs_dt >= dt_90d:
                obs_90d += 1
                if "latitude" in obs and "longitude" in obs:
                    lats.append(float(obs["latitude"]))
                    lons.append(float(obs["longitude"]))

        # 2. Temporal trend calculation (normalized)
        # Expected 14-day count based on 90-day baseline = obs_90d / (90 / 14) ≈ obs_90d / 6.42
        expected_14d = obs_90d / 6.428 if obs_90d > 0 else 0.0
        if expected_14d > 0:
            temporal_trend = (obs_14d - expected_14d) / expected_14d
            temporal_trend = max(-1.0, min(2.0, temporal_trend))
        else:
            temporal_trend = 0.0 if obs_14d == 0 else 1.0

        # 3. NLP threat indicators
        threat_count_30d = 0
        hwc_count = 0
        for th in document_threats:
            threat_count_30d += th.get("mention_count", 1)
            cat = th.get("category_name", "").lower()
            if "conflict" in cat or "crop" in cat:
                hwc_count += th.get("mention_count", 1)

        hwc_ratio = (hwc_count / threat_count_30d) if threat_count_30d > 0 else 0.0

        # 4. Spatial dispersion index
        if len(lats) >= 2:
            spatial_dispersion = float(np.std(lats) + np.std(lons))
        else:
            spatial_dispersion = 0.0

        # 5. Base vulnerability
        iucn_val = cls.IUCN_ORDINAL_MAP.get(iucn_category.upper(), 2.0)

        return {
            "obs_count_recent_14d": float(obs_14d),
            "obs_count_baseline_90d": float(obs_90d),
            "obs_temporal_trend": round(float(temporal_trend), 4),
            "threat_mention_count_30d": float(threat_count_30d),
            "hwc_incident_ratio": round(float(hwc_ratio), 4),
            "spatial_dispersion_std": round(float(spatial_dispersion), 4),
            "iucn_base_vulnerability": float(iucn_val)
        }

    @classmethod
    def features_to_vector(cls, feature_dict: Dict[str, float]) -> List[float]:
        """
        Orders features into canonical array format expected by ML classifiers.
        """
        order = [
            "obs_count_recent_14d",
            "obs_count_baseline_90d",
            "obs_temporal_trend",
            "threat_mention_count_30d",
            "hwc_incident_ratio",
            "spatial_dispersion_std",
            "iucn_base_vulnerability"
        ]
        return [feature_dict.get(k, 0.0) for k in order]
