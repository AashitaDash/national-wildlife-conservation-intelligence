from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.dependencies import get_db
from backend.app.database import engine
from backend.app.models.species import Species
from backend.app.models.observation import Observation
from backend.app.models.document import Document, DocumentThreat
from backend.app.models.threat import Threat
from backend.app.models.ml_outputs import MLRiskScore, MLAnomaly
from backend.app.models.alert import ConservationAlert
from backend.app.schemas.dashboard import (
    SystemStatsResponse,
    ThreatCategorySummary,
    SpeciesRiskSummary,
    HeatmapPoint,
    AlertResponse
)

router = APIRouter(prefix="/dashboards", tags=["Conservation Intelligence Dashboards"])


@router.get("/stats", response_model=SystemStatsResponse)
def get_system_stats(db: Session = Depends(get_db)):
    """
    High-level operational metrics across the conservation data platform.
    """
    total_sp = db.query(Species).count()
    total_obs = db.query(Observation).count()
    total_docs = db.query(Document).count()
    total_th_mentions = db.query(DocumentThreat).count()
    active_anom = db.query(MLAnomaly).filter(MLAnomaly.is_anomaly == True).count()
    crit_species = (
        db.query(MLRiskScore)
        .filter(MLRiskScore.risk_level.in_(["CRITICAL", "HIGH"]))
        .distinct(MLRiskScore.species_id)
        .count()
    )

    db_backend = "PostgreSQL + PostGIS" if "postgresql" in str(engine.url) else "SQLite Fallback (Academic/Dev)"

    return SystemStatsResponse(
        total_species=total_sp,
        total_observations=total_obs,
        total_documents=total_docs,
        total_threat_mentions=int(total_th_mentions),
        active_anomalies=active_anom,
        critical_risk_species=crit_species,
        database_backend=db_backend
    )


@router.get("/heatmap", response_model=List[HeatmapPoint])
def get_observation_heatmap(
    species_id: Optional[int] = Query(None, description="Optional species filter"),
    limit: int = Query(500, le=2000),
    db: Session = Depends(get_db)
):
    """
    Observation spatial distribution coordinates for GIS/Leaflet density heatmaps.
    """
    query = db.query(Observation).join(Species, Observation.species_id == Species.id)
    if species_id:
        query = query.filter(Observation.species_id == species_id)

    records = query.order_by(Observation.observed_at.desc()).limit(limit).all()
    points = []
    for r in records:
        points.append(
            HeatmapPoint(
                latitude=r.latitude,
                longitude=r.longitude,
                weight=1.0,
                species_id=r.species_id,
                species_common_name=r.species.common_name if r.species else "Unknown",
                observed_at=r.observed_at.isoformat()
            )
        )
    return points


@router.get("/threats-summary", response_model=List[ThreatCategorySummary])
def get_threats_summary(db: Session = Depends(get_db)):
    """
    Aggregated threat frequencies extracted from unstructured conservation reports.
    """
    results = (
        db.query(
            Threat.category_name,
            func.count(DocumentThreat.threat_id).label("total_count"),
            Threat.severity_weight
        )
        .join(DocumentThreat, Threat.id == DocumentThreat.threat_id)
        .group_by(Threat.category_name, Threat.severity_weight)
        .order_by(func.count(DocumentThreat.threat_id).desc())
        .all()
    )

    def weight_to_severity(w):
        if w is None:
            return "HIGH"
        if w >= 2.0:
            return "CRITICAL"
        if w >= 1.5:
            return "HIGH"
        if w >= 1.0:
            return "MEDIUM"
        return "LOW"

    return [
        ThreatCategorySummary(
            category_name=r[0],
            count=int(r[1] or 0),
            severity=weight_to_severity(r[2])
        )
        for r in results
    ]


@router.get("/species-risk-ranking", response_model=List[SpeciesRiskSummary])
def get_species_risk_ranking(db: Session = Depends(get_db)):
    """
    Species catalog prioritized by recent ML composite risk scores and threat status.
    Single-pass SQL aggregation for sub-second performance across large catalogs.
    """
    from sqlalchemy import text
    sql = text("""
        SELECT 
            s.id AS species_id, 
            s.common_name, 
            s.scientific_name, 
            s.iucn_category, 
            COALESCE(rs.risk_level, 'MEDIUM') AS risk_level, 
            COALESCE(rs.composite_score, 50.0) AS composite_score, 
            COALESCE(o.cnt, 0) AS observation_count 
        FROM species s 
        LEFT JOIN (
            SELECT DISTINCT ON (species_id) species_id, risk_level, composite_score 
            FROM ml_risk_scores 
            ORDER BY species_id, calculated_at DESC
        ) rs ON s.id = rs.species_id 
        LEFT JOIN (
            SELECT species_id, COUNT(*) AS cnt 
            FROM observations 
            GROUP BY species_id
        ) o ON s.id = o.species_id 
        ORDER BY composite_score DESC;
    """)
    rows = db.execute(sql).fetchall()
    return [
        SpeciesRiskSummary(
            species_id=r[0],
            common_name=r[1],
            scientific_name=r[2],
            iucn_category=r[3],
            risk_level=r[4],
            composite_score=float(r[5]),
            observation_count=int(r[6])
        )
        for r in rows
    ]


@router.get("/alerts", response_model=List[AlertResponse])
def get_conservation_alerts(
    unresolved_only: bool = True,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Real-time conservation intelligence alerts dispatched by the anomaly engine.
    """
    query = db.query(ConservationAlert)
    if unresolved_only:
        query = query.filter(ConservationAlert.is_resolved == False)

    alerts = query.order_by(ConservationAlert.created_at.desc()).limit(limit).all()
    return [
        AlertResponse(
            id=a.id,
            title=a.title,
            description=a.message,
            severity=a.severity,
            species_id=a.species_id,
            species_name=a.species.common_name if a.species else None,
            created_at=a.created_at.isoformat() if a.created_at else ""
        )
        for a in alerts
    ]
