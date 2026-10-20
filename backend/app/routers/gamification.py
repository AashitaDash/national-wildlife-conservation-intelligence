"""
Gamification Router
===================
Exposes researcher profiles, leaderboard, badge catalog, and points ledger.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.dependencies import get_db, get_current_active_user
from backend.app.models.submission import (
    PointsLedger,
    BadgeDefinition,
    UserBadge,
    ObservationSubmission,
)
from backend.app.models.user import User, Role
from backend.app.schemas.submission import ResearcherProfileResponse, LeaderboardEntry
from backend.app.services.gamification_service import GamificationService, user_total_points

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gamification", tags=["Conservation Impact & Gamification"])


@router.get("/profile/me", response_model=ResearcherProfileResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve the authenticated user's gamification profile including
    points, level, badges, and submission statistics.
    """
    return GamificationService.get_researcher_profile(db, current_user.id)


@router.get("/profile/{user_id}", response_model=ResearcherProfileResponse)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Public researcher profile (points and badges only, no submission details)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found.")
    return GamificationService.get_researcher_profile(db, user_id)


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(
    limit: int = Query(25, le=100),
    db: Session = Depends(get_db),
):
    """
    Returns the top researchers ordered by total conservation impact points.
    Shows verified sightings, distinct species, badge count, and level.
    """
    # Aggregate points per user
    point_rows = (
        db.query(
            PointsLedger.user_id,
            func.sum(PointsLedger.amount).label("total_points"),
        )
        .group_by(PointsLedger.user_id)
        .order_by(func.sum(PointsLedger.amount).desc())
        .limit(limit)
        .all()
    )

    entries = []
    for rank, row in enumerate(point_rows, start=1):
        user = db.query(User).filter(User.id == row.user_id).first()
        if not user:
            continue

        verified_count = (
            db.query(ObservationSubmission)
            .filter(
                ObservationSubmission.researcher_id == row.user_id,
                ObservationSubmission.status == "VERIFIED",
            )
            .count()
        )
        distinct_species = (
            db.query(func.count(func.distinct(ObservationSubmission.species_id)))
            .filter(
                ObservationSubmission.researcher_id == row.user_id,
                ObservationSubmission.status == "VERIFIED",
            )
            .scalar()
            or 0
        )
        badge_count = (
            db.query(UserBadge).filter(UserBadge.user_id == row.user_id).count()
        )

        from backend.app.services.gamification_service import get_level
        level_name, _, _ = get_level(row.total_points or 0)

        entries.append(
            LeaderboardEntry(
                rank=rank,
                user_id=row.user_id,
                display_name=user.full_name,
                verified_count=verified_count,
                total_points=int(row.total_points or 0),
                distinct_species=int(distinct_species),
                badge_count=badge_count,
                level=level_name,
            )
        )

    return entries


@router.get("/badges", response_model=List[dict])
def list_badge_catalog(db: Session = Depends(get_db)):
    """Return the full badge catalog with unlock criteria."""
    badges = db.query(BadgeDefinition).order_by(BadgeDefinition.rule_threshold.asc()).all()
    return [
        {
            "code": b.code,
            "name": b.name,
            "description": b.description,
            "icon_emoji": b.icon_emoji,
            "rule_type": b.rule_type,
            "rule_threshold": b.rule_threshold,
        }
        for b in badges
    ]


@router.get("/points/my-ledger")
def get_my_points_ledger(
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return the authenticated user's points ledger (most recent first)."""
    entries = (
        db.query(PointsLedger)
        .filter(PointsLedger.user_id == current_user.id)
        .order_by(PointsLedger.awarded_at.desc())
        .limit(limit)
        .all()
    )
    total = user_total_points(db, current_user.id)
    return {
        "total_points": total,
        "ledger": [
            {
                "id": e.id,
                "amount": e.amount,
                "reason": e.reason,
                "submission_id": e.submission_id,
                "awarded_at": e.awarded_at.isoformat() if e.awarded_at else None,
            }
            for e in entries
        ],
    }
