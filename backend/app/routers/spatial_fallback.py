import json
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.dependencies import get_db, get_optional_user
from backend.app.models.user import User
from backend.app.schemas.spatial import StateBiodiversityMapResponse, StateMetricSummary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/spatial", tags=["Spatial Wildlife Intelligence (Fallback)"])

# Load static GeoJSON for state boundaries (expected location inside the project)
_GEOJSON_PATH = "backend/app/data/india-states.geojson"
try:
    with open(_GEOJSON_PATH, "r", encoding="utf-8") as f:
        _state_geojson = json.load(f)
except Exception as e:
    logger.error(f"Failed to load static GeoJSON: {e}")
    _state_geojson = {"type": "FeatureCollection", "features": []}

def _state_names_from_geojson() -> list:
    """Extract a list of state names from the loaded GeoJSON.
    Supports both 'state_name' and 'NAME_1' property keys.
    """
    names = []
    for feat in _state_geojson.get("features", []):
        props = feat.get("properties", {})
        name = props.get("state_name") or props.get("NAME_1")
        if name:
            names.append(name)
    return names

@router.get("/states", response_model=StateBiodiversityMapResponse)
def get_state_biodiversity_metrics_fallback(
    species_id: int = Query(None),
    taxonomic_group: str = Query(None),
    verification_status: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user),
):
    """Fallback implementation for the /states endpoint.
    It returns a static list of states with empty metric placeholders.
    The optional query parameters are accepted for API compatibility but are ignored
    because spatial joins are unavailable with SQLite.
    """
    # Build empty metrics for each state defined in the static GeoJSON.
    metrics = {}
    for state_name in _state_names_from_geojson():
        metrics[state_name] = StateMetricSummary(
            state_name=state_name,
            distinct_species_count=0,
            total_observation_records=0,
            verified_records=0,
            unverified_records=0,
            taxonomic_breakdown={},
            top_recorded_species=[],
            active_threat_count=0,
            recorded_threats=[],
            highest_risk_level="LOW",
            risk_score_summary=None,
            latest_observations=[],
            data_provenance_sources=[],
        )
    return StateBiodiversityMapResponse(
        total_states_represented=len(_state_names_from_geojson()),
        dataset_disclaimer="Fallback data – no spatial aggregation performed.",
        metric_type="static",
        states=metrics,
    )

