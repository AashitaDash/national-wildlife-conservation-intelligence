import numpy as np
from typing import Dict, Any, Tuple, List


class AcademicHeuristicLabeler:
    """
    Transparent Weak Supervision & Academic Heuristic Ground-Truth Generator.
    
    Academic Rationale:
      Empirical biological extinction probabilities are not directly available via open APIs.
      To train and evaluate supervised classification models without fabricating data,
      we formulate an explicit, defensible multi-criteria heuristic scoring function:
      
        Composite Risk (0-100) =
            0.35 * (IUCN Base Vulnerability * 20)
          + 0.25 * (Observation Decline Penalty)
          + 0.25 * (Threat Density Factor)
          + 0.15 * (Human-Wildlife Conflict Factor)
          
      Tiers:
        - LOW:      0.0 - 29.9
        - MEDIUM:  30.0 - 59.9
        - HIGH:    60.0 - 79.9
        - CRITICAL: >= 80.0
    """

    @classmethod
    def calculate_heuristic_score(cls, features: Dict[str, float]) -> Tuple[float, str]:
        """
        Calculates composite continuous risk score (0-100) and risk level tier.
        """
        # 1. Baseline IUCN Vulnerability component (1.0 - 5.0 -> 20 - 100)
        iucn_val = features.get("iucn_base_vulnerability", 2.0)
        c_iucn = min(100.0, max(20.0, iucn_val * 20.0))

        # 2. Decline penalty: Negative temporal trend increases risk
        trend = features.get("obs_temporal_trend", 0.0)
        if trend < 0:
            c_decline = min(100.0, abs(trend) * 100.0)
        else:
            c_decline = max(0.0, 20.0 - (trend * 20.0))

        # 3. Threat density factor
        threat_count = features.get("threat_mention_count_30d", 0.0)
        c_threat = min(100.0, threat_count * 12.5)

        # 4. Human-Wildlife Conflict factor
        hwc_ratio = features.get("hwc_incident_ratio", 0.0)
        c_hwc = min(100.0, hwc_ratio * 100.0)

        # Weighted combination
        raw_score = (0.35 * c_iucn) + (0.25 * c_decline) + (0.25 * c_threat) + (0.15 * c_hwc)
        score = round(float(np.clip(raw_score, 5.0, 99.5)), 1)

        # Categorical risk level
        if score < 30.0:
            tier = "LOW"
        elif score < 60.0:
            tier = "MEDIUM"
        elif score < 80.0:
            tier = "HIGH"
        else:
            tier = "CRITICAL"

        return score, tier

    @classmethod
    def generate_synthetic_training_dataset(cls, n_samples_per_class: int = 150) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generates an academically grounded, balanced synthetic training distribution
        reflecting conservation archetypes (stable Least Concern, buffer conflict Vulnerable,
        declining Endangered, and acute Critically Endangered).
        
        Returns:
          X: Feature matrix of shape (N, 7)
          y_tier: Categorical labels (LOW, MEDIUM, HIGH, CRITICAL)
          y_scores: Continuous composite risk scores (0-100)
        """
        np.random.seed(42)
        X_list = []
        tier_list = []
        score_list = []

        archetypes = [
            # LOW: Stable population, low threats, LC status
            {"iucn": 1.0, "obs_14": (8, 20), "obs_90": (40, 100), "trend": (0.0, 0.5), "threats": (0, 2), "hwc": (0.0, 0.1)},
            # MEDIUM: Stable or slight decline, moderate threats, VU/NT status
            {"iucn": 3.0, "obs_14": (3, 8), "obs_90": (20, 50), "trend": (-0.2, 0.1), "threats": (2, 5), "hwc": (0.1, 0.3)},
            # HIGH: Noticeable decline, elevated threats, EN status (e.g. Asian Elephant)
            {"iucn": 4.0, "obs_14": (1, 4), "obs_90": (10, 30), "trend": (-0.6, -0.2), "threats": (4, 9), "hwc": (0.3, 0.7)},
            # CRITICAL: Severe collapse, high threat density, CR status (e.g. Great Indian Bustard)
            {"iucn": 5.0, "obs_14": (0, 2), "obs_90": (2, 10), "trend": (-0.9, -0.4), "threats": (7, 15), "hwc": (0.1, 0.5)}
        ]

        for arch in archetypes:
            for _ in range(n_samples_per_class):
                obs_14 = float(np.random.randint(arch["obs_14"][0], arch["obs_14"][1] + 1))
                obs_90 = float(np.random.randint(arch["obs_90"][0], arch["obs_90"][1] + 1))
                trend = float(np.random.uniform(arch["trend"][0], arch["trend"][1]))
                threats = float(np.random.randint(arch["threats"][0], arch["threats"][1] + 1))
                hwc = float(np.random.uniform(arch["hwc"][0], arch["hwc"][1]))
                dispersion = float(np.random.uniform(0.1, 2.5))
                iucn = arch["iucn"]

                feat_dict = {
                    "obs_count_recent_14d": obs_14,
                    "obs_count_baseline_90d": obs_90,
                    "obs_temporal_trend": trend,
                    "threat_mention_count_30d": threats,
                    "hwc_incident_ratio": hwc,
                    "spatial_dispersion_std": dispersion,
                    "iucn_base_vulnerability": iucn
                }

                score, tier = cls.calculate_heuristic_score(feat_dict)
                vector = [obs_14, obs_90, trend, threats, hwc, dispersion, iucn]

                X_list.append(vector)
                tier_list.append(tier)
                score_list.append(score)

        return np.array(X_list), np.array(tier_list), np.array(score_list)
