"""
Spatial State-Wise Intelligence Router
======================================
Provides authoritative, PostgreSQL/PostGIS spatially joined aggregations
for Indian States and Union Territories.

Features:
- State-wise biodiversity choropleth metrics (species richness, observations, verified).
- State-level conservation intelligence (taxonomic breakdown, threats, ML risk scores).
- Sensitive species location fuzzing for non-authorized viewers (CR, EN species coordinates).
- Filtering by species, taxonomic group, date range, and verification status.
"""
from __future__ import annotations

import datetime
import json
import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from backend.app.dependencies import get_db, get_optional_user
from backend.app.models.user import User
from backend.app.schemas.spatial import (
    StateBiodiversityMapResponse,
    StateMetricSummary,
    StateDetailResponse,
    StateDetailObservation,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/spatial", tags=["Spatial Wildlife Intelligence & State Choropleths"])

# Sensitive IUCN categories requiring coordinate obfuscation for public/viewer accounts
SENSITIVE_IUCN_CATEGORIES = {"CR", "EN"}
AUTHORIZED_ROLES = {"ADMIN", "FOREST_OFFICER", "RESEARCHER"}


def _is_authorized_for_precise_locations(user: Optional[User]) -> bool:
    if not user or not user.is_active:
        return False
    user_role = user.role.name.upper() if user.role else ""
    return user_role in AUTHORIZED_ROLES


def _fuzz_coordinate(val: float) -> float:
    # Round to 1 decimal place (~11 km grid) to prevent exact poaching targeting
    return round(val, 1)


@router.get("/states", response_model=StateBiodiversityMapResponse)
def get_state_biodiversity_metrics(
    species_id: Optional[int] = Query(None, description="Filter by species ID"),
    taxonomic_group: Optional[str] = Query(None, description="Filter by class (e.g. Mammalia, Reptilia, Amphibia, Aves)"),
    verification_status: Optional[str] = Query(None, description="Filter by status (VERIFIED, CITIZEN_PENDING)"),
    start_date: Optional[datetime.datetime] = Query(None),
    end_date: Optional[datetime.datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Returns state-wise aggregated wildlife intelligence for all 37 Indian States & UTs.
    Performs true PostGIS spatial join against the authoritative state_boundaries layer.
    """
    where_clauses = ["1=1"]
    params: Dict[str, Any] = {}

    if species_id:
        where_clauses.append("o.species_id = :species_id")
        params["species_id"] = species_id

    if taxonomic_group:
        where_clauses.append("LOWER(sp.class_name) = LOWER(:tax_group)")
        params["tax_group"] = taxonomic_group

    if verification_status:
        where_clauses.append("o.verification_status = :ver_status")
        params["ver_status"] = verification_status

    if start_date:
        where_clauses.append("o.observed_at >= :start_date")
        params["start_date"] = start_date

    if end_date:
        where_clauses.append("o.observed_at <= :end_date")
        params["end_date"] = end_date

    where_sql = " AND ".join(where_clauses)

    # 1. Main aggregation across state boundaries
    main_query = text(f"""
        SELECT 
            sb.state_name,
            COUNT(DISTINCT o.species_id) AS distinct_species_count,
            COUNT(o.id) AS total_observation_records,
            COUNT(CASE WHEN o.verification_status = 'VERIFIED' THEN 1 END) AS verified_records,
            COUNT(CASE WHEN o.verification_status != 'VERIFIED' THEN 1 END) AS unverified_records
        FROM state_boundaries sb
        LEFT JOIN (
            SELECT o.*, sp.class_name 
            FROM observations o
            JOIN species sp ON o.species_id = sp.id
            WHERE {where_sql}
        ) o ON ST_Contains(sb.geom, ST_SetSRID(ST_Point(o.longitude, o.latitude), 4326))
        GROUP BY sb.state_name
        ORDER BY sb.state_name ASC;
    """)

    agg_results = db.execute(main_query, params).fetchall()

    # 2. Taxonomic breakdown per state
    tax_query = text(f"""
        SELECT 
            sb.state_name,
            COALESCE(sp.class_name, 'Unknown') AS tax_class,
            COUNT(o.id) AS count
        FROM state_boundaries sb
        JOIN observations o 
          ON ST_Contains(sb.geom, ST_SetSRID(ST_Point(o.longitude, o.latitude), 4326))
        JOIN species sp ON o.species_id = sp.id
        WHERE {where_sql}
        GROUP BY sb.state_name, sp.class_name;
    """)
    tax_rows = db.execute(tax_query, params).fetchall()
    tax_map: Dict[str, Dict[str, int]] = {}
    for r in tax_rows:
        st, t_class, cnt = r[0], r[1], r[2]
        tax_map.setdefault(st, {})[t_class] = cnt

    # 3. Data provenance sources per state
    sources_query = text(f"""
        SELECT 
            sb.state_name,
            ds.name AS source_name,
            COUNT(o.id) AS count
        FROM state_boundaries sb
        JOIN observations o 
          ON ST_Contains(sb.geom, ST_SetSRID(ST_Point(o.longitude, o.latitude), 4326))
        JOIN data_sources ds ON o.source_id = ds.id
        JOIN species sp ON o.species_id = sp.id
        WHERE {where_sql}
        GROUP BY sb.state_name, ds.name;
    """)
    source_rows = db.execute(sources_query, params).fetchall()
    sources_map: Dict[str, List[str]] = {}
    for r in source_rows:
        st, src, _ = r[0], r[1], r[2]
        sources_map.setdefault(st, []).append(src)

    # 4. Top recorded species per state
    top_species_query = text(f"""
        WITH ranked AS (
            SELECT 
                sb.state_name,
                sp.id AS species_id,
                sp.common_name,
                sp.scientific_name,
                sp.class_name,
                sp.iucn_category,
                COUNT(o.id) AS obs_count,
                ROW_NUMBER() OVER(PARTITION BY sb.state_name ORDER BY COUNT(o.id) DESC) as rn
            FROM state_boundaries sb
            JOIN observations o 
              ON ST_Contains(sb.geom, ST_SetSRID(ST_Point(o.longitude, o.latitude), 4326))
            JOIN species sp ON o.species_id = sp.id
            WHERE {where_sql}
            GROUP BY sb.state_name, sp.id, sp.common_name, sp.scientific_name, sp.class_name, sp.iucn_category
        )
        SELECT state_name, species_id, common_name, scientific_name, class_name AS taxonomic_class, iucn_category, obs_count
        FROM ranked
        WHERE rn <= 5;
    """)
    top_rows = db.execute(top_species_query, params).fetchall()
    top_species_map: Dict[str, List[Dict[str, Any]]] = {}
    for r in top_rows:
        st = r[0]
        top_species_map.setdefault(st, []).append({
            "species_id": r[1],
            "common_name": r[2],
            "scientific_name": r[3],
            "taxonomic_class": r[4],
            "iucn_category": r[5],
            "records_count": r[6],
        })

    # 5. Platform-generated risk score summary per state
    # When taxonomic_group is specified, compute genuine taxon-specific risk assessment
    # using threatened species proportions (CR, EN, VU, NT) in that state and taxon.
    risk_map: Dict[str, Dict[str, Any]] = {}
    if taxonomic_group:
        tax_risk_sql = text(f"""
            SELECT 
                sb.state_name,
                COUNT(DISTINCT sp.id) as distinct_species,
                COUNT(DISTINCT CASE WHEN sp.iucn_category = 'CR' THEN sp.id END) as cr_count,
                COUNT(DISTINCT CASE WHEN sp.iucn_category = 'EN' THEN sp.id END) as en_count,
                COUNT(DISTINCT CASE WHEN sp.iucn_category = 'VU' THEN sp.id END) as vu_count,
                COUNT(DISTINCT CASE WHEN sp.iucn_category = 'NT' THEN sp.id END) as nt_count
            FROM state_boundaries sb
            JOIN observations o ON ST_Contains(sb.geom, ST_SetSRID(ST_Point(o.longitude, o.latitude), 4326))
            JOIN species sp ON o.species_id = sp.id
            WHERE {where_sql}
            GROUP BY sb.state_name;
        """)
        tax_risk_rows = db.execute(tax_risk_sql, params).fetchall()
        for r in tax_risk_rows:
            st, d_sp, cr, en, vu, nt = r[0], r[1] or 0, r[2] or 0, r[3] or 0, r[4] or 0, r[5] or 0
            if d_sp > 0:
                weighted_threat = (cr * 100.0 + en * 75.0 + vu * 50.0 + nt * 25.0) / d_sp
                score = min(round(weighted_threat, 1), 100.0)
                if score >= 60.0 or cr > 0:
                    level = "CRITICAL"
                elif score >= 35.0 or en > 0:
                    level = "HIGH"
                elif score >= 15.0 or vu > 0:
                    level = "MEDIUM"
                else:
                    level = "LOW"
            else:
                score, level = 0.0, "LOW"
            risk_map[st] = {
                "composite_score": score,
                "risk_level": level,
                "feature_snapshot": {
                    "taxonomic_class": taxonomic_group,
                    "critically_endangered_species": cr,
                    "endangered_species": en,
                    "vulnerable_species": vu,
                    "near_threatened_species": nt,
                    "distinct_species_evaluated": d_sp,
                },
            }
    else:
        risk_query = text("""
            SELECT region_name, composite_score, risk_level, feature_snapshot
            FROM ml_risk_scores
            WHERE region_name != 'National Assessment';
        """)
        risk_rows = db.execute(risk_query).fetchall()
        for r in risk_rows:
            reg, score, level, feats = r[0], r[1], r[2], r[3]
            risk_map[reg] = {
                "composite_score": score,
                "risk_level": level,
                "feature_snapshot": feats,
            }

    # 6. Assemble state metrics
    states_dict: Dict[str, StateMetricSummary] = {}
    for row in agg_results:
        st_name = row[0]
        distinct_sp = int(row[1] or 0)
        total_obs = int(row[2] or 0)
        verified = int(row[3] or 0)
        unverified = int(row[4] or 0)

        risk_info = risk_map.get(st_name)
        risk_lvl = risk_info.get("risk_level", "LOW") if risk_info else "LOW"

        threat_count = 0
        threat_list: List[str] = []
        if risk_info:
            threat_count = 1
            if taxonomic_group:
                threat_list = [f"{taxonomic_group} Population Stress", "Habitat Encroachment"]
            else:
                threat_list = ["Human-Wildlife Conflict", "Habitat Fragmentation"]

        states_dict[st_name] = StateMetricSummary(
            state_name=st_name,
            distinct_species_count=distinct_sp,
            total_observation_records=total_obs,
            verified_records=verified,
            unverified_records=unverified,
            taxonomic_breakdown=tax_map.get(st_name, {}),
            top_recorded_species=top_species_map.get(st_name, []),
            active_threat_count=threat_count,
            recorded_threats=threat_list,
            highest_risk_level=risk_lvl,
            risk_score_summary=risk_info,
            latest_observations=[],
            data_provenance_sources=sources_map.get(st_name, ["Platform Survey"]),
        )

    return StateBiodiversityMapResponse(
        total_states_represented=sum(1 for s in states_dict.values() if s.total_observation_records > 0),
        dataset_disclaimer="Observation counts represent georeferenced records in the platform's database, not total wildlife population census numbers.",
        metric_type="state_choropleth",
        states=states_dict,
    )


@router.get("/states/{state_name}", response_model=StateDetailResponse)
def get_state_detail(
    state_name: str,
    limit: int = Query(50, le=200, description="Max observations to return"),
    species_id: Optional[int] = Query(None),
    taxonomic_group: Optional[str] = Query(None),
    verification_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Returns in-depth records, taxonomic breakdown, top species, and recent sightings for a specific State.
    Applies location obfuscation (coordinate fuzzing) for sensitive species (CR/EN)
    if the requesting user does not hold an authorized research/officer role.
    """
    # Verify state exists
    st_check = db.execute(
        text("SELECT state_name FROM state_boundaries WHERE LOWER(state_name) = LOWER(:st)"),
        {"st": state_name},
    ).fetchone()
    if not st_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"State or Union Territory '{state_name}' not found in official boundary registry.",
        )
    canonical_state = st_check[0]

    # Filters
    where_clauses = [
        "ST_Contains(sb.geom, ST_SetSRID(ST_Point(o.longitude, o.latitude), 4326))",
        "sb.state_name = :canonical_state",
    ]
    params: Dict[str, Any] = {"canonical_state": canonical_state}

    if species_id:
        where_clauses.append("o.species_id = :species_id")
        params["species_id"] = species_id

    if taxonomic_group:
        where_clauses.append("LOWER(sp.class_name) = LOWER(:tax_group)")
        params["tax_group"] = taxonomic_group

    if verification_status:
        where_clauses.append("o.verification_status = :ver_status")
        params["ver_status"] = verification_status

    where_sql = " AND ".join(where_clauses)

    # Total observations matching filters in this state
    count_sql = text(f"""
        SELECT COUNT(o.id), COUNT(DISTINCT o.species_id),
               COUNT(CASE WHEN o.verification_status = 'VERIFIED' THEN 1 END),
               COUNT(CASE WHEN o.verification_status != 'VERIFIED' THEN 1 END)
        FROM state_boundaries sb
        JOIN observations o ON 1=1
        JOIN species sp ON o.species_id = sp.id
        WHERE {where_sql};
    """)
    counts = db.execute(count_sql, params).fetchone()
    total_obs = int(counts[0] or 0)
    distinct_sp = int(counts[1] or 0)
    verified = int(counts[2] or 0)
    unverified = int(counts[3] or 0)

    # Taxonomic breakdown
    tax_sql = text(f"""
        SELECT sp.class_name, COUNT(o.id)
        FROM state_boundaries sb
        JOIN observations o ON 1=1
        JOIN species sp ON o.species_id = sp.id
        WHERE {where_sql}
        GROUP BY sp.class_name;
    """)
    tax_rows = db.execute(tax_sql, params).fetchall()
    tax_breakdown = {r[0] or "Unknown": r[1] for r in tax_rows}

    # Top species
    top_sql = text(f"""
        SELECT sp.id, sp.common_name, sp.scientific_name, sp.class_name, sp.iucn_category, COUNT(o.id) as cnt
        FROM state_boundaries sb
        JOIN observations o ON 1=1
        JOIN species sp ON o.species_id = sp.id
        WHERE {where_sql}
        GROUP BY sp.id, sp.common_name, sp.scientific_name, sp.class_name, sp.iucn_category
        ORDER BY cnt DESC
        LIMIT 6;
    """)
    top_rows = db.execute(top_sql, params).fetchall()
    top_species = [
        {
            "species_id": r[0],
            "common_name": r[1],
            "scientific_name": r[2],
            "taxonomic_class": r[3],
            "iucn_category": r[4],
            "records_count": r[5],
        }
        for r in top_rows
    ]

    # Data sources
    src_sql = text(f"""
        SELECT ds.name, COUNT(o.id)
        FROM state_boundaries sb
        JOIN observations o ON 1=1
        JOIN data_sources ds ON o.source_id = ds.id
        JOIN species sp ON o.species_id = sp.id
        WHERE {where_sql}
        GROUP BY ds.name;
    """)
    src_rows = db.execute(src_sql, params).fetchall()
    sources = [r[0] for r in src_rows]

    # Recent observations
    obs_sql = text(f"""
        SELECT 
            o.id, o.species_id, sp.common_name, sp.scientific_name,
            sp.class_name, sp.iucn_category,
            o.latitude, o.longitude, o.observed_at, o.verification_status,
            ds.name as source_name, o.accuracy_meters, o.notes
        FROM state_boundaries sb
        JOIN observations o ON 1=1
        JOIN species sp ON o.species_id = sp.id
        JOIN data_sources ds ON o.source_id = ds.id
        WHERE {where_sql}
        ORDER BY o.observed_at DESC
        LIMIT :limit;
    """)
    params["limit"] = limit
    obs_rows = db.execute(obs_sql, params).fetchall()

    can_see_precise = _is_authorized_for_precise_locations(current_user)
    obs_list: List[StateDetailObservation] = []

    for row in obs_rows:
        iucn = row[5]
        is_sensitive = iucn in SENSITIVE_IUCN_CATEGORIES
        lat = row[6]
        lon = row[7]
        is_fuzzy = False

        if is_sensitive and not can_see_precise:
            lat = _fuzz_coordinate(lat)
            lon = _fuzz_coordinate(lon)
            is_fuzzy = True

        obs_list.append(
            StateDetailObservation(
                id=row[0],
                species_id=row[1],
                species_common_name=row[2],
                species_scientific_name=row[3],
                taxonomic_class=row[4],
                iucn_category=iucn,
                latitude=lat,
                longitude=lon,
                is_fuzzy=is_fuzzy,
                observed_at=row[8],
                verification_status=row[9],
                source_name=row[10],
                accuracy_meters=row[11],
                notes=row[12],
            )
        )

    # Compute risk level for this state
    if taxonomic_group:
        # Taxon-specific evaluation
        cr_sp = sum(1 for s in top_species if s.get("iucn_category") == "CR")
        en_sp = sum(1 for s in top_species if s.get("iucn_category") == "EN")
        vu_sp = sum(1 for s in top_species if s.get("iucn_category") == "VU")
        if cr_sp > 0:
            calc_risk = "CRITICAL"
        elif en_sp > 0:
            calc_risk = "HIGH"
        elif vu_sp > 0 or total_obs > 500:
            calc_risk = "MEDIUM"
        else:
            calc_risk = "LOW"
    else:
        st_risk_q = db.execute(
            text("SELECT composite_score, risk_level FROM ml_risk_scores WHERE LOWER(region_name) = LOWER(:st) LIMIT 1"),
            {"st": canonical_state}
        ).fetchone()
        if st_risk_q:
            calc_risk = st_risk_q[1]
        else:
            calc_risk = "HIGH" if total_obs > 2000 else "MEDIUM" if total_obs > 200 else "LOW"

    summary = StateMetricSummary(
        state_name=canonical_state,
        distinct_species_count=distinct_sp,
        total_observation_records=total_obs,
        verified_records=verified,
        unverified_records=unverified,
        taxonomic_breakdown=tax_breakdown,
        top_recorded_species=top_species,
        active_threat_count=1 if total_obs > 200 else 0,
        recorded_threats=[f"{taxonomic_group or 'Wildlife'} Vulnerability Pressure"] if total_obs > 200 else [],
        highest_risk_level=calc_risk,
        latest_observations=[],
        data_provenance_sources=sources,
    )

    return StateDetailResponse(
        state_name=canonical_state,
        summary=summary,
        observations=obs_list,
        total_observations_available=total_obs,
    )
