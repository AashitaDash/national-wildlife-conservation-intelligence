import os
import logging
from typing import Dict, Any, List
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

logger = logging.getLogger("wildlife_platform.ml.anomaly")


class AnomalyDetectorService:
    """
    Unsupervised Spatial-Temporal Outlier Detection using Isolation Forest.
    Identifies anomalous observation drops (potential extirpation/sensor dropout)
    or acute incident surges (poaching spikes, forest fires, conflict outbreaks).
    """

    FEATURE_NAMES = [
        "obs_count_recent_14d",
        "obs_temporal_trend",
        "threat_mention_count_30d",
        "hwc_incident_ratio",
        "spatial_dispersion_std"
    ]

    def __init__(self, model_dir: str = None, contamination: float = 0.08):
        if not model_dir:
            model_dir = os.path.join(os.path.dirname(__file__), "models")
        os.makedirs(model_dir, exist_ok=True)
        self.model_path = os.path.join(model_dir, "isolation_forest.joblib")
        self.contamination = contamination
        self.model = None
        self._load_or_train()

    def _load_or_train(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                logger.info(f"Loaded trained IsolationForest from {self.model_path}")
                return
            except Exception as e:
                logger.warning(f"Could not load IsolationForest ({e}). Retraining...")

        self.train_and_save()

    def train_and_save(self) -> Dict[str, Any]:
        """
        Trains Isolation Forest on standard baseline operational distributions.
        """
        np.random.seed(42)
        # Generate representative normal observations (92%) and historical outliers (8%)
        n_normal = 460
        n_anomalous = 40

        # Normal distribution
        obs_14_norm = np.random.uniform(3, 20, n_normal)
        trend_norm = np.random.uniform(-0.3, 0.4, n_normal)
        threats_norm = np.random.uniform(0, 5, n_normal)
        hwc_norm = np.random.uniform(0, 0.3, n_normal)
        disp_norm = np.random.uniform(0.2, 1.8, n_normal)

        X_normal = np.column_stack([obs_14_norm, trend_norm, threats_norm, hwc_norm, disp_norm])

        # Anomalous distribution (sharp drops or acute threat spikes)
        obs_14_anom = np.concatenate([np.random.uniform(0, 1, 20), np.random.uniform(25, 45, 20)])
        trend_anom = np.concatenate([np.random.uniform(-0.95, -0.6, 20), np.random.uniform(1.2, 2.5, 20)])
        threats_anom = np.random.uniform(10, 25, n_anomalous)
        hwc_anom = np.random.uniform(0.6, 1.0, n_anomalous)
        disp_anom = np.random.uniform(2.5, 5.0, n_anomalous)

        X_anomalous = np.column_stack([obs_14_anom, trend_anom, threats_anom, hwc_anom, disp_anom])
        X = np.vstack([X_normal, X_anomalous])

        logger.info(f"Training IsolationForest on {len(X)} baseline samples...")
        iso = IsolationForest(n_estimators=100, contamination=self.contamination, random_state=42)
        iso.fit(X)

        self.model = iso
        joblib.dump(iso, self.model_path)
        logger.info(f"IsolationForest model saved to {self.model_path}")

        return {
            "status": "trained",
            "samples_trained": len(X),
            "contamination": self.contamination
        }

    def detect_anomaly(self, feature_dict: Dict[str, float]) -> Dict[str, Any]:
        """
        Evaluates input features for spatial-temporal anomaly.
        Returns is_anomaly (bool), anomaly_score (float), and causal explanation.
        """
        vector = [feature_dict.get(k, 0.0) for k in self.FEATURE_NAMES]
        X = np.array([vector])

        if self.model is None:
            # Fallback heuristic rule
            trend = feature_dict.get("obs_temporal_trend", 0.0)
            threats = feature_dict.get("threat_mention_count_30d", 0.0)
            is_anom = trend <= -0.65 or threats >= 10.0
            return {
                "is_anomaly": is_anom,
                "anomaly_score": -0.5 if is_anom else 0.5,
                "anomaly_type": "INCIDENT_SURGE" if threats >= 10.0 else "OBSERVATION_DROP",
                "explanation": "Heuristic fallback anomaly check"
            }

        # Isolation Forest prediction: -1 = outlier, 1 = inlier
        pred = self.model.predict(X)[0]
        # Raw decision function: lower / negative values signify deeper anomaly
        score = float(self.model.decision_function(X)[0])
        is_anom = bool(pred == -1)

        # Generate causal diagnosis
        trend = feature_dict.get("obs_temporal_trend", 0.0)
        threats = feature_dict.get("threat_mention_count_30d", 0.0)
        obs_14 = feature_dict.get("obs_count_recent_14d", 0.0)

        anomaly_type = "NORMAL"
        explanation = "Observation dynamics within expected baseline bounds."

        if is_anom:
            if threats >= 7.0:
                anomaly_type = "INCIDENT_SURGE"
                explanation = f"Acute threat surge detected ({int(threats)} mentions in 30 days). Significant deviation from baseline."
            elif trend <= -0.50:
                anomaly_type = "OBSERVATION_DROP"
                pct = int(abs(trend) * 100)
                explanation = f"Abrupt observation decline detected ({pct}% below 90-day baseline rate). Potential sensor dropout or local habitat disturbance."
            else:
                anomaly_type = "SPATIAL_DISPERSAL"
                explanation = "Unusual geographic dispersal pattern observed outside standard sanctuary corridors."

        return {
            "is_anomaly": is_anom,
            "anomaly_score": round(score, 4),
            "anomaly_type": anomaly_type,
            "explanation": explanation
        }
