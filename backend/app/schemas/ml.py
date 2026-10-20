from typing import Optional, Dict, Any, List
from pydantic import BaseModel
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
    species: Dict[str, Any]
    location: Optional[Dict[str, Any]] = None
    period: Dict[str, Any]
    observation_count: int
    related_threats: List[ThreatContext]
    related_documents: List[DocumentContext]
    supporting_record_count: int
    explanation: str
    investigation_guidance: str
    evidence_strength: str

    class Config:
        from_attributes = True


class ModelMetricsResponse(BaseModel):
    classifier: Dict[str, Any]
    anomaly_detector: Dict[str, Any]
