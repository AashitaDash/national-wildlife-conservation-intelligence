from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime


class StateMetricSummary(BaseModel):
    state_name: str
    distinct_species_count: int
    total_observation_records: int
    verified_records: int
    unverified_records: int
    taxonomic_breakdown: Dict[str, int]
    top_recorded_species: List[Dict[str, Any]]
    active_threat_count: int
    recorded_threats: List[str]
    highest_risk_level: Optional[str] = "LOW"
    risk_score_summary: Optional[Dict[str, Any]] = None
    latest_observations: List[Dict[str, Any]]
    data_provenance_sources: List[str]


class StateBiodiversityMapResponse(BaseModel):
    total_states_represented: int
    dataset_disclaimer: str
    metric_type: str
    states: Dict[str, StateMetricSummary]


class StateDetailObservation(BaseModel):
    id: int
    species_id: int
    species_common_name: Optional[str] = None
    species_scientific_name: Optional[str] = None
    taxonomic_class: Optional[str] = None
    iucn_category: Optional[str] = None
    latitude: float
    longitude: float
    is_fuzzy: bool = False
    observed_at: datetime
    verification_status: str
    source_name: Optional[str] = None
    accuracy_meters: Optional[float] = None
    notes: Optional[str] = None


class StateDetailResponse(BaseModel):
    state_name: str
    summary: StateMetricSummary
    observations: List[StateDetailObservation]
    total_observations_available: int
