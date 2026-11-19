from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class RiskAssessmentRequest(BaseModel):
    species_id: int
    location_id: Optional[int] = None
    override_features: Optional[Dict[str, float]] = None


class RiskAssessmentResponse(BaseModel):
    species_id: int
    species_common_name: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    composite_score: float  # 0 - 100
    class_probabilities: Dict[str, float]
    feature_vector: Dict[str, float]
    is_anomaly: bool
    anomaly_score: float
    diagnostic_reason: str
    assessed_at: datetime


class ThreatContext(BaseModel):
    category_name: str
    mention_count: int

class DocumentContext(BaseModel):
    id: int
    title: str

class AnomalyItem(BaseModel):
    id: int
    anomaly_type: str
    isolation_score: float
    score_interpretation: str
    operational_severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    species: Dict[str, Any]
    location: Optional[Dict[str, Any]] = None
    period: Dict[str, Any]
    observation_count: int
    expected_baseline: Optional[float] = None
    deviation_percentage: Optional[float] = None
    related_threats: List[ThreatContext]
    related_documents: List[DocumentContext]
    supporting_record_count: int
    explanation: str
    hypotheses: List[str]
    investigation_guidance: str
    evidence_strength: str  # HIGH, MEDIUM, LOW, INSUFFICIENT
    fingerprint: Optional[str] = None
    status: str = "OPEN"  # OPEN, ACKNOWLEDGED, UNDER_INVESTIGATION, RESOLVED
    acknowledged: bool = False
    acknowledged_by_id: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    investigation_notes: Optional[str] = None
    detected_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AcknowledgeAnomalyRequest(BaseModel):
    notes: Optional[str] = None
    status: Optional[str] = "ACKNOWLEDGED"  # ACKNOWLEDGED, UNDER_INVESTIGATION, RESOLVED


class ModelMetricsResponse(BaseModel):
    classifier: Dict[str, Any]
    anomaly_detector: Dict[str, Any]

