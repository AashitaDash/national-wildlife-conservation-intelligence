from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class SystemStatsResponse(BaseModel):
    total_species: int
    total_observations: int
    total_documents: int
    total_threat_mentions: int
    active_anomalies: int
    critical_risk_species: int
    database_backend: str


class ThreatCategorySummary(BaseModel):
    category_name: str
    count: int
    severity: str


class SpeciesRiskSummary(BaseModel):
    species_id: int
    common_name: str
    scientific_name: str
    iucn_category: str
    risk_level: str
    composite_score: float
    observation_count: int


class HeatmapPoint(BaseModel):
    latitude: float
    longitude: float
    weight: float
    species_id: int
    species_common_name: str
    observed_at: str


class AlertResponse(BaseModel):
    id: int
    title: str
    description: str
    severity: str
    alert_type: Optional[str] = "ECOLOGICAL_ANOMALY"
    species_id: Optional[int] = None
    species_name: Optional[str] = None
    is_resolved: Optional[bool] = False
    created_at: str
