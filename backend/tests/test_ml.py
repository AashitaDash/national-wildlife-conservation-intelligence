"""
Wildlife Conservation Intelligence Platform - ML Pipeline Tests
Validates feature engineering, weak supervision, risk classification, and anomaly detection.
"""

import os
import pytest
import datetime
from ml.feature_engineering import FeatureEngineeringService
from ml.heuristic_labeler import AcademicHeuristicLabeler
from ml.risk_classifier import RiskClassifierService
from ml.anomaly_detector import AnomalyDetectorService


def test_feature_engineering_service():
    now = datetime.datetime.now(datetime.timezone.utc)
    
    observations = [
        {"observed_at": (now - datetime.timedelta(days=2)).isoformat(), "latitude": 21.5, "longitude": 86.3},
        {"observed_at": (now - datetime.timedelta(days=5)).isoformat(), "latitude": 21.6, "longitude": 86.4},
        {"observed_at": (now - datetime.timedelta(days=20)).isoformat(), "latitude": 21.7, "longitude": 86.2},
        {"observed_at": (now - datetime.timedelta(days=50)).isoformat(), "latitude": 21.8, "longitude": 86.1},
    ]
    
    threats = [
        {"category_name": "Human-Wildlife Conflict", "mention_count": 3},
        {"category_name": "Poaching", "mention_count": 2},
    ]
    
    features = FeatureEngineeringService.compute_features_for_species_region(
        species_id=1,
        iucn_category="EN",
        observations=observations,
        document_threats=threats,
        current_time=now
    )
    
    assert features["obs_count_recent_14d"] == 2.0
    assert features["obs_count_baseline_90d"] == 4.0
    assert features["threat_mention_count_30d"] == 5.0
    assert features["hwc_incident_ratio"] == 0.6  # 3/5
    assert features["iucn_base_vulnerability"] == 4.0  # EN = 4.0
    
    vec = FeatureEngineeringService.features_to_vector(features)
    assert len(vec) == 7
    assert vec[0] == 2.0
    assert vec[1] == 4.0


def test_academic_heuristic_labeler():
    # Low risk profile
    low_features = {
        "obs_count_recent_14d": 15.0,
        "obs_count_baseline_90d": 60.0,
        "obs_temporal_trend": 0.2,
        "threat_mention_count_30d": 0.0,
        "hwc_incident_ratio": 0.0,
        "spatial_dispersion_std": 0.5,
        "iucn_base_vulnerability": 1.0  # LC
    }
    score_low, tier_low = AcademicHeuristicLabeler.calculate_heuristic_score(low_features)
    assert tier_low in ["LOW", "MEDIUM"]
    assert score_low < 40.0

    # High risk profile
    crit_features = {
        "obs_count_recent_14d": 1.0,
        "obs_count_baseline_90d": 25.0,
        "obs_temporal_trend": -0.8,
        "threat_mention_count_30d": 10.0,
        "hwc_incident_ratio": 0.75,
        "spatial_dispersion_std": 0.1,
        "iucn_base_vulnerability": 5.0  # CR
    }
    score_crit, tier_crit = AcademicHeuristicLabeler.calculate_heuristic_score(crit_features)
    assert tier_crit in ["HIGH", "CRITICAL"]
    assert score_crit > 60.0


def test_synthetic_cohort_generation():
    X, tiers, scores = AcademicHeuristicLabeler.generate_synthetic_training_dataset(n_samples_per_class=25)
    assert len(X) == 100
    assert len(tiers) == 100
    assert len(scores) == 100
    for vec, tier in zip(X[:10], tiers[:10]):
        assert len(vec) == 7
        assert tier in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def test_risk_classifier_prediction():
    service = RiskClassifierService()
    # Model should already be trained and saved by scripts/train_models.py
    if not os.path.exists(service.model_path):
        service.train_and_save()
        
    test_features = {
        "obs_count_recent_14d": 2.0,
        "obs_count_baseline_90d": 10.0,
        "obs_temporal_trend": -0.3,
        "threat_mention_count_30d": 6.0,
        "hwc_incident_ratio": 0.5,
        "spatial_dispersion_std": 0.3,
        "iucn_base_vulnerability": 4.0
    }
    
    pred = service.predict(test_features)
    assert pred["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert 0 <= pred["composite_score"] <= 100
    assert "probabilities" in pred
    assert len(pred["probabilities"]) > 0


def test_anomaly_detector_prediction():
    service = AnomalyDetectorService()
    if not os.path.exists(service.model_path):
        service.train_and_save()
        
    test_features = {
        "obs_count_recent_14d": 0.0,
        "obs_count_baseline_90d": 25.0,
        "obs_temporal_trend": -0.9,
        "threat_mention_count_30d": 12.0,
        "hwc_incident_ratio": 0.8,
        "spatial_dispersion_std": 0.05,
        "iucn_base_vulnerability": 5.0
    }
    
    result = service.detect_anomaly(test_features)
    assert "is_anomaly" in result
    assert isinstance(result["is_anomaly"], bool)
    assert "anomaly_score" in result
    assert "explanation" in result
