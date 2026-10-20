import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.risk_classifier import RiskClassifierService
from ml.anomaly_detector import AnomalyDetectorService
from ml.feature_engineering import FeatureEngineeringService


def main():
    print("=" * 70)
    print(" WILDLIFE CONSERVATION INTELLIGENCE PLATFORM - ML TRAINING ENGINE")
    print(" [Task: Supervised Risk Classifier + Unsupervised Isolation Forest]")
    print("=" * 70)

    # 1. Train Risk Classifier
    print("\n[1/2] Training Conservation Risk Classifier (Random Forest)...")
    risk_service = RiskClassifierService()
    metrics = risk_service.train_and_save()

    print(f"  Test Accuracy: {metrics['accuracy'] * 100:.2f}%")
    print(f"  Macro F1:      {metrics['macro_f1']:.4f}")
    print("\n  Feature Importances:")
    for feat, imp in metrics["feature_importances"].items():
        bar = "#" * int(imp * 40)
        print(f"    - {feat.ljust(25)} : {imp:.4f} {bar}")

    # 2. Train Isolation Forest Anomaly Detector
    print("\n[2/2] Training Spatial-Temporal Isolation Forest...")
    anomaly_service = AnomalyDetectorService()
    anom_metrics = anomaly_service.train_and_save()
    print(f"  Isolation Forest status: {anom_metrics['status']}")
    print(f"  Contamination threshold: {anom_metrics['contamination'] * 100:.1f}%")
    print(f"  Trained samples:         {anom_metrics['samples_trained']}")

    # 3. Benchmark Verification: Asian Elephant in Odisha
    print("\n" + "-" * 70)
    print(" BENCHMARK INFERENCE: Asian Elephant (Odisha / Similipal Sector)")
    print("-" * 70)

    test_features = {
        "obs_count_recent_14d": 3.0,
        "obs_count_baseline_90d": 9.0,
        "obs_temporal_trend": -0.28,
        "threat_mention_count_30d": 8.0,
        "hwc_incident_ratio": 0.62,
        "spatial_dispersion_std": 0.45,
        "iucn_base_vulnerability": 4.0  # Endangered (EN)
    }

    pred = risk_service.predict(test_features)
    anom = anomaly_service.detect_anomaly(test_features)

    print(f"  Predicted Risk Level: {pred['risk_level']}")
    print(f"  Composite Risk Score: {pred['composite_score']}/100")
    print(f"  Class Probabilities:  {pred['probabilities']}")
    print(f"  Anomaly Detected:     {anom['is_anomaly']} (Score: {anom['anomaly_score']})")
    print(f"  Diagnostic Reason:    {anom['explanation']}")

    print("=" * 70)
    print(" ML Model training and verification completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()
