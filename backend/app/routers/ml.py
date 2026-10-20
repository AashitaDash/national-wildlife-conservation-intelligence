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
from backend.app.schemas.ml import RiskAssessmentRequest, RiskAssessmentResponse, AnomalyItem, ModelMetricsResponse

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
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Retrieve active ecological anomalies detected by the Isolation Forest,
    contextualized with Conservation Anomaly Intelligence.
    """
    from backend.app.models.document import DocumentSpecies, DocumentThreat, Document
    from sqlalchemy import func

    query = db.query(MLAnomaly)
    if active_only:
        query = query.filter(MLAnomaly.is_anomaly == True)

    records = query.order_by(MLAnomaly.detected_at.desc()).offset(skip).limit(limit).all()
    results = []
    
    thirty_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)

    for r in records:
        # Context 1: Observations
        obs_count = db.query(Observation).filter(
            Observation.species_id == r.species_id,
            Observation.observed_at >= thirty_days_ago
        ).count()

        # Context 2: Documents
        docs = db.query(Document).join(DocumentSpecies).filter(
            DocumentSpecies.species_id == r.species_id
        ).limit(5).all()
        related_documents = [{"id": d.id, "title": d.title} for d in docs]
        
        # Context 3: Threats
        threat_query = db.query(Threat.category_name, func.count(DocumentThreat.document_id).label("mention_count")).\
            join(DocumentThreat, Threat.id == DocumentThreat.threat_id).\
            join(DocumentSpecies, DocumentThreat.document_id == DocumentSpecies.document_id).\
            filter(DocumentSpecies.species_id == r.species_id).\
            group_by(Threat.category_name).\
            order_by(func.count(DocumentThreat.document_id).desc()).\
            limit(3).all()
            
        related_threats = [{"category_name": t[0], "mention_count": t[1]} for t in threat_query]

        doc_count = len(related_documents)
        if doc_count >= 5:
            evidence_strength = "HIGH"
        elif doc_count >= 2:
            evidence_strength = "MEDIUM"
        elif doc_count == 1:
            evidence_strength = "LOW"
        else:
            evidence_strength = "INSUFFICIENT"

        # Safe parsing
        species_dict = {
            "id": r.species_id,
            "common_name": r.species.common_name if r.species else "Unknown",
            "scientific_name": r.species.scientific_name if r.species else "Unknown"
        }
        location_dict = {
            "id": r.location_id,
            "name": r.location.name if r.location else "Unknown Region"
        } if r.location_id else None

        results.append(
            AnomalyItem(
                id=r.id,
                anomaly_type=r.anomaly_type,
                isolation_score=r.anomaly_score,
                species=species_dict,
                location=location_dict,
                period={"days": 30, "label": "Last 30 days"},
                observation_count=obs_count,
                related_threats=related_threats,
                related_documents=related_documents,
                supporting_record_count=obs_count + doc_count,
                explanation=r.explanation or "An unusual observation pattern was detected.",
                investigation_guidance="Review the associated observations, recent conservation documents, and field reports to determine whether the pattern represents a meaningful ecological or reporting change.",
                evidence_strength=evidence_strength,
                detected_at=r.detected_at
            )
        )
    return results


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
