from typing import List, Optional
import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from backend.app.dependencies import get_db, get_current_user, require_roles
from backend.app.models.observation import Observation, DataSource
from backend.app.models.species import Species
from backend.app.models.location import Location
from backend.app.models.user import User
from backend.app.schemas.observation import ObservationResponse, ObservationCreate
from ingestion.cleaner import DataCleanerService

router = APIRouter(prefix="/observations", tags=["Observations & Field Telemetry"])


def _to_observation_response(obs: Observation) -> ObservationResponse:
    return ObservationResponse(
        id=obs.id,
        species_id=obs.species_id,
        location_id=obs.location_id,
        source_id=obs.source_id,
        submitted_by_user_id=obs.submitted_by_user_id,
        observed_at=obs.observed_at,
        latitude=obs.latitude,
        longitude=obs.longitude,
        accuracy_meters=obs.accuracy_meters,
        verification_status=obs.verification_status,
        notes=obs.notes,
        raw_metadata=obs.raw_metadata,
        created_at=obs.created_at,
        species_common_name=obs.species.common_name if obs.species else None,
        species_scientific_name=obs.species.scientific_name if obs.species else None,
        species_image_url=obs.species.image_url if obs.species else None,
        source_name=obs.source.name if obs.source else None,
        location_name=obs.location.name if obs.location else None
    )


@router.get("", response_model=List[ObservationResponse])
def list_observations(
    species_id: Optional[int] = Query(None, description="Filter by species ID"),
    location_id: Optional[int] = Query(None, description="Filter by protected area location ID"),
    verification_status: Optional[str] = Query(None, description="Filter status (e.g. VERIFIED, CITIZEN_PENDING)"),
    start_date: Optional[datetime.datetime] = Query(None),
    end_date: Optional[datetime.datetime] = Query(None),
    min_lat: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None),
    min_lon: Optional[float] = Query(None),
    max_lon: Optional[float] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Spatially and temporally filter observation records.
    Supports bounding box queries, date intervals, and species taxonomy filters.
    """
    query = db.query(Observation)
    if species_id:
        query = query.filter(Observation.species_id == species_id)
    if location_id:
        query = query.filter(Observation.location_id == location_id)
    if verification_status:
        query = query.filter(Observation.verification_status == verification_status)
    if start_date:
        query = query.filter(Observation.observed_at >= start_date)
    if end_date:
        query = query.filter(Observation.observed_at <= end_date)
    if min_lat is not None:
        query = query.filter(Observation.latitude >= min_lat)
    if max_lat is not None:
        query = query.filter(Observation.latitude <= max_lat)
    if min_lon is not None:
        query = query.filter(Observation.longitude >= min_lon)
    if max_lon is not None:
        query = query.filter(Observation.longitude <= max_lon)

    records = query.order_by(Observation.observed_at.desc()).offset(skip).limit(limit).all()
    return [_to_observation_response(r) for r in records]


@router.get("/map", response_model=List[ObservationResponse])
def get_map_observations(
    species_id: Optional[int] = Query(None, description="Filter by species ID"),
    taxonomic_group: Optional[str] = Query(None, description="Filter by class (e.g. Mammalia, Aves, Reptilia, Amphibia)"),
    state_name: Optional[str] = Query(None, description="Filter by state using PostGIS spatial containment"),
    min_lat: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None),
    min_lon: Optional[float] = Query(None),
    max_lon: Optional[float] = Query(None),
    limit: int = Query(1000, le=2000, description="Max markers to return"),
    db: Session = Depends(get_db)
):
    """
    Map-specific endpoint for fetching observations.
    When state_name is provided, uses PostGIS ST_Contains against state_boundaries
    to return only observations physically within that state polygon.
    When taxonomic_group is provided, filters observations by the species class_name.
    Returns a diverse random sample if no species_id is provided, to ensure multiple species are represented.
    """
    # If state_name is provided, use a raw PostGIS spatial join for accurate containment
    if state_name:
        from sqlalchemy import text
        where_extra = []
        params = {"state_name": state_name, "limit": limit}
        if species_id:
            where_extra.append("o.species_id = :species_id")
            params["species_id"] = species_id
        if taxonomic_group:
            where_extra.append("LOWER(sp.class_name) = LOWER(:tax_group)")
            params["tax_group"] = taxonomic_group
        
        extra_sql = ("AND " + " AND ".join(where_extra)) if where_extra else ""

        sql = text(f"""
            SELECT o.id
            FROM observations o
            JOIN state_boundaries sb ON ST_Contains(sb.geom, ST_SetSRID(ST_Point(o.longitude, o.latitude), 4326))
            JOIN species sp ON o.species_id = sp.id
            WHERE LOWER(sb.state_name) = LOWER(:state_name)
            {extra_sql}
            ORDER BY o.observed_at DESC NULLS LAST
            LIMIT :limit
        """)
        result = db.execute(sql, params)
        obs_ids = [row[0] for row in result.fetchall()]
        if not obs_ids:
            return []
        records = db.query(Observation).filter(Observation.id.in_(obs_ids)).all()
        return [_to_observation_response(r) for r in records]

    query = db.query(Observation)
    if species_id:
        query = query.filter(Observation.species_id == species_id)
    if taxonomic_group:
        query = query.join(Species, Observation.species_id == Species.id).filter(func.lower(Species.class_name) == taxonomic_group.lower())
    if min_lat is not None:
        query = query.filter(Observation.latitude >= min_lat)
    if max_lat is not None:
        query = query.filter(Observation.latitude <= max_lat)
    if min_lon is not None:
        query = query.filter(Observation.longitude >= min_lon)
    if max_lon is not None:
        query = query.filter(Observation.longitude <= max_lon)
    
    if species_id or taxonomic_group:
        records = query.order_by(Observation.observed_at.desc()).limit(limit).all()
    else:
        records = query.order_by(func.random()).limit(limit).all()
        
    return [_to_observation_response(r) for r in records]


@router.get("/{obs_id}", response_model=ObservationResponse)
def get_observation(obs_id: int, db: Session = Depends(get_db)):
    """
    Fetch a single observation record with related species and source provenance.
    """
    obs = db.query(Observation).filter(Observation.id == obs_id).first()
    if not obs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Observation ID {obs_id} not found")
    return _to_observation_response(obs)


@router.post("", response_model=ObservationResponse, status_code=status.HTTP_201_CREATED)
def create_observation(
    obs_in: ObservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a field observation. Validates geographic coordinates against Indian territorial boundaries.
    """
    # 1. Geographic validation
    is_valid_geo, geo_err = DataCleanerService.validate_coordinates(obs_in.latitude, obs_in.longitude)
    if not is_valid_geo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=geo_err)

    # 2. Species existence check
    species = db.query(Species).filter(Species.id == obs_in.species_id).first()
    if not species:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Species ID {obs_in.species_id} does not exist.")

    # 3. Source resolution
    source_name = obs_in.source_name or "Citizen Science Portal"
    source = db.query(DataSource).filter(DataSource.name == source_name).first()
    if not source:
        source = DataSource(name=source_name, description="Field Submissions")
        db.add(source)
        db.flush()

    # Determine default verification status based on role
    user_role = current_user.role.name.upper() if current_user.role else "VIEWER"
    status_val = "VERIFIED" if user_role in ["ADMIN", "ECOLOGIST", "RANGER", "FOREST_OFFICER"] else "CITIZEN_PENDING"

    obs = Observation(
        species_id=obs_in.species_id,
        location_id=obs_in.location_id,
        submitted_by_user_id=current_user.id,
        source_id=source.id,
        observed_at=obs_in.observed_at,
        latitude=obs_in.latitude,
        longitude=obs_in.longitude,
        accuracy_meters=obs_in.accuracy_meters,
        verification_status=status_val,
        notes=obs_in.notes,
        raw_metadata=obs_in.raw_metadata or {}
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return _to_observation_response(obs)


@router.put("/{obs_id}/verify", response_model=ObservationResponse)
def verify_observation(
    obs_id: int,
    status_action: str = Query("VERIFIED", enum=["VERIFIED", "REJECTED", "FLAGGED"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "ECOLOGIST", "RANGER", "FOREST_OFFICER"))
):
    """
    Verify or flag a pending field observation. Restricted to Field Rangers, Ecologists, and Admins.
    """
    obs = db.query(Observation).filter(Observation.id == obs_id).first()
    if not obs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Observation ID {obs_id} not found")

    obs.verification_status = status_action
    db.commit()
    db.refresh(obs)
    return _to_observation_response(obs)
