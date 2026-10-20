from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.app.dependencies import get_db, require_roles
from sqlalchemy import func
from backend.app.models.species import Species
from backend.app.models.observation import Observation
from backend.app.models.ml_outputs import MLRiskScore, MLAnomaly
from backend.app.schemas.species import SpeciesResponse, SpeciesDetailResponse, SpeciesCreate, SpeciesUpdate, PaginatedSpeciesResponse

router = APIRouter(prefix="/species", tags=["Species Catalog & Biodiversity"])


@router.get("", response_model=PaginatedSpeciesResponse)
def list_species(
    iucn_category: Optional[str] = Query(None, description="Filter by IUCN status (e.g. CR, EN, VU, LC)"),
    search: Optional[str] = Query(None, description="Search by common or scientific name"),
    skip: int = 0,
    limit: int = 24,
    db: Session = Depends(get_db)
):
    """
    List species catalog with optional IUCN status and keyword filters.
    """
    query = db.query(Species)
    if iucn_category:
        query = query.filter(Species.iucn_category == iucn_category.upper())
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            (Species.common_name.ilike(pattern)) | (Species.scientific_name.ilike(pattern))
        )
    total = query.count()
    items = query.order_by(Species.common_name).offset(skip).limit(limit).all()
    
    if items:
        species_ids = [s.id for s in items]
        obs_counts = dict(
            db.query(Observation.species_id, func.count(Observation.id))
            .filter(Observation.species_id.in_(species_ids))
            .group_by(Observation.species_id)
            .all()
        )
        for s in items:
            s.total_observations = obs_counts.get(s.id, 0)
            
    page = (skip // limit) + 1 if limit > 0 else 1
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": limit
    }


@router.get("/{species_id}", response_model=SpeciesDetailResponse)
def get_species_detail(species_id: int, db: Session = Depends(get_db)):
    """
    Retrieve comprehensive species intelligence including observation metrics and recent risk assessments.
    """
    species = db.query(Species).filter(Species.id == species_id).first()
    if not species:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Species ID {species_id} not found")

    obs_count = db.query(Observation).filter(Observation.species_id == species_id).count()
    recent_risk = (
        db.query(MLRiskScore)
        .filter(MLRiskScore.species_id == species_id)
        .order_by(MLRiskScore.calculated_at.desc())
        .first()
    )
    active_anomalies = (
        db.query(MLAnomaly)
        .filter(MLAnomaly.species_id == species_id, MLAnomaly.is_anomaly == True)
        .count()
    )

    detail = SpeciesDetailResponse(
        id=species.id,
        scientific_name=species.scientific_name,
        common_name=species.common_name,
        kingdom=species.kingdom,
        phylum=species.phylum,
        class_name=species.class_name,
        order_name=species.order_name,
        family=species.family,
        genus=species.genus,
        iucn_category=species.iucn_category,
        description=species.description,
        image_url=species.image_url,
        created_at=species.created_at,
        total_observations=obs_count,
        recent_risk_level=recent_risk.risk_level if recent_risk else "UNKNOWN",
        recent_risk_score=recent_risk.composite_score if recent_risk else None,
        active_anomalies_count=active_anomalies
    )
    return detail


@router.post("", response_model=SpeciesResponse, status_code=status.HTTP_201_CREATED)
def create_species(
    species_in: SpeciesCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "ECOLOGIST", "RESEARCHER"))
):
    """
    Add a new species to the authoritative catalog. Restricted to authorized researchers/ecologists.
    """
    existing = db.query(Species).filter(Species.scientific_name == species_in.scientific_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Species '{species_in.scientific_name}' already exists."
        )

    species = Species(**species_in.model_dump())
    db.add(species)
    db.commit()
    db.refresh(species)
    return species


@router.put("/{species_id}", response_model=SpeciesResponse)
def update_species(
    species_id: int,
    species_in: SpeciesUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "ECOLOGIST"))
):
    """
    Update taxonomic details or IUCN classification for a species.
    """
    species = db.query(Species).filter(Species.id == species_id).first()
    if not species:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Species ID {species_id} not found")

    update_data = species_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(species, field, val)

    db.commit()
    db.refresh(species)
    return species
