from typing import List, Optional
import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.app.dependencies import get_db, require_roles
from backend.app.models.species import Species
from backend.app.models.location import Location
from backend.app.models.observation import Observation
from backend.app.models.document import DocumentThreat
from backend.app.models.threat import Threat
from backend.app.models.ml_outputs import MLRiskScore, MLAnomaly
from backend.app.models.alert import ConservationAlert
from backend.app.schemas.ml import (
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    AnomalyItem,
    ModelMetricsResponse,
    AcknowledgeAnomalyRequest
)
from backend.app.models.user import User

from ml.feature_engineering import FeatureEngineeringService
from ml.risk_classifier import RiskClassifierService
from ml.anomaly_detector import AnomalyDetectorService

router = APIRouter(prefix="/ml", tags=["Machine Learning & Risk Intelligence"])

_risk_service = None
_anomaly_service = None


def get_ml_services():
    global _risk_service, _anomaly_service
    if _risk_service is None:
        _risk_service = RiskClassifierService()
    if _anomaly_service is None:
        _anomaly_service = AnomalyDetectorService()
    return _risk_service, _anomaly_service


@router.post("/assess-risk", response_model=RiskAssessmentResponse)
def assess_species_risk(
    req: RiskAssessmentRequest,
    db: Session = Depends(get_db)
):
    """
    Compute real-time conservation risk assessment:
    Extracts spatio-temporal observations, NLP threat frequencies, and calculates
    Random Forest risk tier + Isolation Forest anomaly detection score.
    """
    species = db.query(Species).filter(Species.id == req.species_id).first()
    if not species:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Species ID {req.species_id} not found")

    risk_service, anomaly_service = get_ml_services()
    now = datetime.datetime.now(datetime.timezone.utc)

    # 1. Fetch species observations
    obs_query = db.query(Observation).filter(Observation.species_id == req.species_id)
    if req.location_id:
        obs_query = obs_query.filter(Observation.location_id == req.location_id)
    raw_obs = [
        {"observed_at": o.observed_at, "latitude": o.latitude, "longitude": o.longitude}
        for o in obs_query.all()
    ]

    # 2. Fetch recent document threat associations
    dt_records = (
        db.query(DocumentThreat, Threat.category_name)
        .join(Threat, DocumentThreat.threat_id == Threat.id)
        .all()
    )
    raw_threats = [
        {"category_name": rec[1], "mention_count": 1}
        for rec in dt_records
    ]

    # 3. Extract spatio-temporal features
    features = FeatureEngineeringService.compute_features_for_species_region(
        species_id=species.id,
        iucn_category=species.iucn_category,
        observations=raw_obs,
        document_threats=raw_threats,
        current_time=now
    )

    # Allow simulation overrides if provided
    if req.override_features:
        for k, v in req.override_features.items():
            if k in features:
                features[k] = float(v)

    # 4. Predict Supervised Risk Level
    prediction = risk_service.predict(features)

    # 5. Predict Unsupervised Ecological Anomaly
    anomaly_res = anomaly_service.detect_anomaly(features)

    # 6. Record MLRiskScore to Database
    ml_record = MLRiskScore(
        species_id=species.id,
        region_name="National Assessment",
        risk_level=prediction["risk_level"],
        composite_score=prediction["composite_score"],
        observation_frequency=features.get("obs_count_recent_14d"),
        threat_density=features.get("threat_mention_count_30d"),
        temporal_trend=features.get("obs_temporal_trend"),
        feature_snapshot=features,
        calculated_at=now
    )
    db.add(ml_record)

    # 7. Record MLAnomaly if flagged
    if anomaly_res["is_anomaly"]:
        anom_record = MLAnomaly(
            species_id=species.id,
            location_id=req.location_id,
            anomaly_score=anomaly_res["anomaly_score"],
            anomaly_type="SPATIAL_TEMPORAL_DEVIATION",
            explanation=anomaly_res["explanation"],
            is_anomaly=True,
            detected_at=now
        )
        db.add(anom_record)
        db.flush()

        # Trigger ConservationAlert for critical or anomalous conditions
        alert = ConservationAlert(
            title=f"Ecological Anomaly: {species.common_name}",
            alert_type="ANOMALY_DETECTED",
            message=f"Automated risk intelligence flagged anomaly: {anomaly_res['explanation']}",
            severity="CRITICAL" if prediction["risk_level"] == "CRITICAL" else "WARNING",
            species_id=species.id,
            location_id=req.location_id,
            is_resolved=False,
            created_at=now
        )
        db.add(alert)

    db.commit()

    return RiskAssessmentResponse(
        species_id=species.id,
        species_common_name=species.common_name,
        risk_level=prediction["risk_level"],
        composite_score=prediction["composite_score"],
        class_probabilities=prediction["probabilities"],
        feature_vector=features,
        is_anomaly=anomaly_res["is_anomaly"],
        anomaly_score=anomaly_res["anomaly_score"],
        diagnostic_reason=anomaly_res["explanation"],
        assessed_at=now
    )


@router.get("/anomalies", response_model=List[AnomalyItem])
def list_active_anomalies(
    active_only: bool = True,
    deduplicate: bool = True,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Retrieve active ecological anomalies detected by the Isolation Forest,
    contextualized with Actionable Conservation Anomaly Intelligence.
    Answers: What changed? Against what baseline? Over what window?
    Separates statistical anomaly score, operational severity, and evidence confidence.
    """
    from backend.app.models.document import DocumentSpecies, DocumentThreat, Document
    from sqlalchemy import func
    import hashlib

    query = db.query(MLAnomaly)
    if active_only:
        query = query.filter(MLAnomaly.is_anomaly == True)

    records = query.order_by(MLAnomaly.detected_at.desc()).offset(skip).limit(limit * 3 if deduplicate else limit).all()
    results = []
    seen_fingerprints = set()

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    t30 = now_utc - datetime.timedelta(days=30)
    t90 = now_utc - datetime.timedelta(days=90)

    for r in records:
        # Stable fingerprint: species_id + location_id + anomaly_type + detection month
        month_str = r.detected_at.strftime("%Y-%m") if r.detected_at else "current"
        fingerprint_raw = f"{r.species_id}:{r.location_id or 0}:{r.anomaly_type}:{month_str}"
        fingerprint = hashlib.sha256(fingerprint_raw.encode("utf-8")).hexdigest()[:16]

        if deduplicate and fingerprint in seen_fingerprints:
            continue
        seen_fingerprints.add(fingerprint)

        # 1. Real observation count in recent 30-day window
        obs_count = db.query(Observation).filter(
            Observation.species_id == r.species_id,
            Observation.observed_at >= t30
        ).count()

        # 2. Historical baseline: 90-day window normalized to 30 days
        obs_90d = db.query(Observation).filter(
            Observation.species_id == r.species_id,
            Observation.observed_at >= t90
        ).count()
        expected_baseline = round(obs_90d / 3.0, 1)

        # Calculate deviation percentage if baseline is meaningful
        if expected_baseline > 0:
            dev_pct = round(((obs_count - expected_baseline) / expected_baseline) * 100.0, 1)
        else:
            dev_pct = None

        # 3. Contextual evidence: scientific documents
        docs = db.query(Document).join(DocumentSpecies).filter(
            DocumentSpecies.species_id == r.species_id
        ).limit(5).all()
        related_documents = [{"id": d.id, "title": d.title} for d in docs]
        doc_count = len(related_documents)

        # 4. Contextual evidence: active threat mentions
        threat_query = db.query(Threat.category_name, func.count(DocumentThreat.document_id).label("mention_count")).\
            join(DocumentThreat, Threat.id == DocumentThreat.threat_id).\
            join(DocumentSpecies, DocumentThreat.document_id == DocumentSpecies.document_id).\
            filter(DocumentSpecies.species_id == r.species_id).\
            group_by(Threat.category_name).\
            order_by(func.count(DocumentThreat.document_id).desc()).\
            limit(3).all()
        related_threats = [{"category_name": t[0], "mention_count": t[1]} for t in threat_query]

        # 5. Evidence confidence (Volume and ground-truth supporting data)
        if doc_count >= 3 and obs_count >= 10:
            evidence_strength = "HIGH"
        elif doc_count >= 1 or obs_count >= 5:
            evidence_strength = "MEDIUM"
        elif obs_count > 0:
            evidence_strength = "LOW"
        else:
            evidence_strength = "INSUFFICIENT"

        # 6. Score Interpretation (Isolation Forest decision function: lower / more negative = deeper outlier)
        iso = r.anomaly_score
        if iso < -0.15:
            score_interp = f"Severe statistical outlier (score {iso:.3f} << 0 threshold; deep isolation tree branch depth)"
        elif iso < -0.05:
            score_interp = f"Moderate statistical outlier (score {iso:.3f} < 0 threshold; unusual multi-feature combination)"
        elif iso < 0.0:
            score_interp = f"Marginal outlier (score {iso:.3f} near boundary; potential boundary fluctuation)"
        else:
            score_interp = f"Nominal baseline zone (score {iso:.3f} >= 0; inlier distribution)"

        # 7. Operational Severity (Separated from raw model score)
        # Combines anomaly depth + presence of critical threats + magnitude of deviation
        threat_names = [t["category_name"].lower() for t in related_threats]
        has_severe_threat = any("poaching" in tn or "fragmentation" in tn or "snaring" in tn or "conflict" in tn for tn in threat_names)

        if (iso < -0.12 and has_severe_threat) or (dev_pct is not None and dev_pct <= -65.0):
            operational_severity = "CRITICAL"
        elif iso < -0.05 or has_severe_threat:
            operational_severity = "HIGH"
        elif iso < 0.0:
            operational_severity = "MEDIUM"
        else:
            operational_severity = "LOW"

        # 8. Hypotheses: What might explain this? (Labeled explicitly as working hypotheses)
        hypotheses = []
        if dev_pct is not None and dev_pct < -40.0:
            hypotheses.append("Hypothesis A: Local patrol or sensor coverage dropout during reporting period.")
            hypotheses.append("Hypothesis B: Spatial displacement of herd/individuals away from human disturbance or linear infrastructure.")
            hypotheses.append("Hypothesis C: Acute mortality or severe localized poaching/snaring pressure.")
        elif dev_pct is not None and dev_pct > 50.0:
            hypotheses.append("Hypothesis A: Seasonal congregation around remaining water bodies or food resources.")
            hypotheses.append("Hypothesis B: Increased survey effort or targeted community reporting.")
        else:
            hypotheses.append("Hypothesis A: Uncorrelated environmental fluctuation within standard seasonal tolerance.")
            hypotheses.append("Hypothesis B: Sporadic multi-jurisdictional migration between corridor segments.")

        # 9. Investigation Guidance for Field Officers & Researchers
        guidance = (
            f"1. Cross-reference recent telemetry from {r.location.name if r.location else 'monitored sectors'} against patrol logs. "
            f"2. Inspect high-frequency threat zones ({', '.join([t['category_name'] for t in related_threats[:2]]) or 'unclassified'}). "
            f"3. Verify sensor uptime before confirming ecological disruption."
        )

        species_dict = {
            "id": r.species_id,
            "common_name": r.species.common_name if r.species else "Unknown",
            "scientific_name": r.species.scientific_name if r.species else "Unknown"
        }
        location_dict = {
            "id": r.location_id,
            "name": r.location.name if r.location else "Core Habitat Corridor"
        } if r.location_id else None

        results.append(
            AnomalyItem(
                id=r.id,
                anomaly_type=r.anomaly_type,
                isolation_score=r.anomaly_score,
                score_interpretation=score_interp,
                operational_severity=operational_severity,
                species=species_dict,
                location=location_dict,
                period={"days": 30, "label": "Last 30 days vs 90-day baseline"},
                observation_count=obs_count,
                expected_baseline=expected_baseline,
                deviation_percentage=dev_pct,
                related_threats=related_threats,
                related_documents=related_documents,
                supporting_record_count=obs_count + doc_count,
                explanation=r.explanation or "Unusual observation density flagged by isolation forest.",
                hypotheses=hypotheses,
                investigation_guidance=guidance,
                evidence_strength=evidence_strength,
                fingerprint=fingerprint,
                status=r.status or ("ACKNOWLEDGED" if r.acknowledged else "OPEN"),
                acknowledged=bool(r.acknowledged),
                acknowledged_by_id=r.acknowledged_by_id,
                acknowledged_at=r.acknowledged_at,
                investigation_notes=r.investigation_notes,
                detected_at=r.detected_at
            )
        )
        if len(results) >= limit:
            break

    return results


@router.post("/anomalies/{anomaly_id}/acknowledge")
def acknowledge_anomaly(
    anomaly_id: int,
    body: Optional[AcknowledgeAnomalyRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "FOREST_OFFICER", "RESEARCHER"]))
):
    """
    Acknowledge an anomaly, persist the review status, recording user ID,
    timestamp, and optional investigation notes. Restricted to authorized roles.
    """
    anom = db.query(MLAnomaly).filter(MLAnomaly.id == anomaly_id).first()
    if not anom:
        raise HTTPException(status_code=404, detail="Anomaly record not found")

    target_status = (body.status if body and body.status else "ACKNOWLEDGED").upper()
    valid_statuses = {"ACKNOWLEDGED", "UNDER_INVESTIGATION", "RESOLVED", "OPEN"}
    if target_status not in valid_statuses:
        target_status = "ACKNOWLEDGED"

    try:
        anom.status = target_status
        anom.acknowledged = (target_status != "OPEN")
        anom.acknowledged_by_id = current_user.id
        anom.acknowledged_at = datetime.datetime.now(datetime.timezone.utc)
        if body and body.notes:
            anom.investigation_notes = body.notes.strip()

        db.commit()
        db.refresh(anom)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist anomaly acknowledgement: {str(exc)}"
        )

    return {
        "status": "success",
        "id": anom.id,
        "investigation_status": anom.status,
        "acknowledged": anom.acknowledged,
        "acknowledged_by_id": anom.acknowledged_by_id,
        "acknowledged_at": anom.acknowledged_at.isoformat() if anom.acknowledged_at else None,
        "investigation_notes": anom.investigation_notes,
        "message": f"Anomaly #{anom.id} status updated to {anom.status} by {current_user.email}"
    }


@router.get("/metrics")
def get_model_metrics():
    """
    Returns diagnostic metrics and feature importances for trained ML models.
    """
    risk_service, anomaly_service = get_ml_services()
    return {
        "risk_classifier": {
            "model_type": "RandomForestClassifier",
            "n_estimators": 100,
            "classes": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            "features": list(risk_service.FEATURE_NAMES)
        },
        "anomaly_detector": {
            "model_type": "IsolationForest",
            "contamination": anomaly_service.contamination,
            "features": list(anomaly_service.FEATURE_NAMES)
        }
    }


@router.post("/retrain", dependencies=[Depends(require_roles("ADMIN", "ECOLOGIST"))])
def retrain_models():
    """
    Retrain risk classification and anomaly detection models. Restricted to Admins and Ecologists.
    """
    risk_service, anomaly_service = get_ml_services()
    clf_metrics = risk_service.train_and_save()
    anom_metrics = anomaly_service.train_and_save()
    return {
        "message": "Models retrained successfully",
        "risk_classifier_metrics": clf_metrics,
        "anomaly_detector_metrics": anom_metrics
    }
