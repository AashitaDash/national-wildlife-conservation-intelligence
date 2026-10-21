from typing import List, Optional, Literal
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
    Returns a diverse species-distributed sample when no species_id is provided,
    avoiding slow ORDER BY random() full-table scans.
    """
    from sqlalchemy import text as sa_text

    # --- State-filtered path: PostGIS spatial containment ---
    if state_name:
        where_extra = []
        params: dict = {"state_name": state_name, "lim": limit}
        if species_id:
            where_extra.append("o.species_id = :species_id")
            params["species_id"] = species_id
        if taxonomic_group:
            where_extra.append("LOWER(sp.class_name) = LOWER(:tax_group)")
            params["tax_group"] = taxonomic_group

        extra_sql = ("AND " + " AND ".join(where_extra)) if where_extra else ""
        sql = sa_text(f"""
            SELECT
                o.id, o.species_id, o.location_id, o.source_id, o.submitted_by_user_id,
                o.observed_at, o.latitude, o.longitude, o.accuracy_meters,
                o.verification_status, o.notes, o.raw_metadata, o.created_at,
                sp.common_name AS species_common_name,
                sp.scientific_name AS species_scientific_name,
                sp.image_url AS species_image_url,
                ds.name AS source_name,
                NULL::text AS location_name
            FROM observations o
            JOIN state_boundaries sb
                ON ST_Contains(sb.geom, ST_SetSRID(ST_Point(o.longitude, o.latitude), 4326))
            JOIN species sp ON o.species_id = sp.id
            LEFT JOIN data_sources ds ON o.source_id = ds.id
            WHERE LOWER(sb.state_name) = LOWER(:state_name)
            {extra_sql}
            ORDER BY o.observed_at DESC NULLS LAST
            LIMIT :lim
        """)
        rows = db.execute(sql, params).fetchall()
        return [_row_to_response(r) for r in rows]

    # --- Build WHERE clauses for non-spatial path ---
    where_parts = ["1=1"]
    params2: dict = {"lim": limit}

    if species_id:
        where_parts.append("o.species_id = :species_id")
        params2["species_id"] = species_id
    if taxonomic_group:
        where_parts.append("LOWER(sp.class_name) = LOWER(:tax_group)")
        params2["tax_group"] = taxonomic_group
    if min_lat is not None:
        where_parts.append("o.latitude >= :min_lat")
        params2["min_lat"] = min_lat
    if max_lat is not None:
        where_parts.append("o.latitude <= :max_lat")
        params2["max_lat"] = max_lat
    if min_lon is not None:
        where_parts.append("o.longitude >= :min_lon")
        params2["min_lon"] = min_lon
    if max_lon is not None:
        where_parts.append("o.longitude <= :max_lon")
        params2["max_lon"] = max_lon

    where_sql = " AND ".join(where_parts)
    join_species = "JOIN species sp ON o.species_id = sp.id" if taxonomic_group else "LEFT JOIN species sp ON o.species_id = sp.id"

    if species_id or taxonomic_group:
        # Targeted query: most-recent observations first, no sampling needed
        order_clause = "ORDER BY o.observed_at DESC NULLS LAST"
    else:
        # Diverse sample: pick up to `limit // per_species` per species using
        # row_number() OVER (PARTITION BY species_id ORDER BY observed_at DESC).
        # This avoids ORDER BY random() which causes a full sequential scan.
        per_species = max(1, limit // 50)  # 50 species × 20 each = 1000 default
        params2["per_sp"] = per_species
        order_clause = "ORDER BY o.species_id, o.observed_at DESC NULLS LAST"
        # Wrap with a CTE to apply per-species cap
        cte_sql = sa_text(f"""
            WITH ranked AS (
                SELECT
                    o.id, o.species_id, o.location_id, o.source_id, o.submitted_by_user_id,
                    o.observed_at, o.latitude, o.longitude, o.accuracy_meters,
                    o.verification_status, o.notes, o.raw_metadata, o.created_at,
                    sp.common_name AS species_common_name,
                    sp.scientific_name AS species_scientific_name,
                    sp.image_url AS species_image_url,
                    ds.name AS source_name,
                    NULL::text AS location_name,
                    ROW_NUMBER() OVER (
                        PARTITION BY o.species_id
                        ORDER BY o.observed_at DESC NULLS LAST
                    ) AS rn
                FROM observations o
                {join_species}
                LEFT JOIN data_sources ds ON o.source_id = ds.id
                WHERE {where_sql}
            )
            SELECT id, species_id, location_id, source_id, submitted_by_user_id,
                   observed_at, latitude, longitude, accuracy_meters,
                   verification_status, notes, raw_metadata, created_at,
                   species_common_name, species_scientific_name, species_image_url,
                   source_name, location_name
            FROM ranked
            WHERE rn <= :per_sp
            LIMIT :lim
        """)
        rows = db.execute(cte_sql, params2).fetchall()
        return [_row_to_response(r) for r in rows]

    # Standard path (species_id or taxonomic_group provided)
    flat_sql = sa_text(f"""
        SELECT
            o.id, o.species_id, o.location_id, o.source_id, o.submitted_by_user_id,
            o.observed_at, o.latitude, o.longitude, o.accuracy_meters,
            o.verification_status, o.notes, o.raw_metadata, o.created_at,
            sp.common_name AS species_common_name,
            sp.scientific_name AS species_scientific_name,
            sp.image_url AS species_image_url,
            ds.name AS source_name,
            NULL::text AS location_name
        FROM observations o
        {join_species}
        LEFT JOIN data_sources ds ON o.source_id = ds.id
        WHERE {where_sql}
        {order_clause}
        LIMIT :lim
    """)
    rows = db.execute(flat_sql, params2).fetchall()
    return [_row_to_response(r) for r in rows]


def _row_to_response(r) -> ObservationResponse:
    """Convert a raw SQL row (from map queries) to ObservationResponse without ORM lazy-loads."""
    return ObservationResponse(
        id=r[0],
        species_id=r[1],
        location_id=r[2],
        source_id=r[3],
        submitted_by_user_id=r[4],
        observed_at=r[5],
        latitude=r[6],
        longitude=r[7],
        accuracy_meters=r[8],
        verification_status=r[9],
        notes=r[10],
        raw_metadata=r[11],
        created_at=r[12],
        species_common_name=r[13],
        species_scientific_name=r[14],
        species_image_url=r[15],
        source_name=r[16],
        location_name=r[17],
    )


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
    status_action: Literal["VERIFIED", "REJECTED", "FLAGGED"] = "VERIFIED",
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
