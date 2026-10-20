"""
Gamification Service
====================
Awards points, badges, and levels based on verified researcher contributions.
All operations are idempotent — repeated calls cannot create duplicate rewards.
Points are stored in an append-only ledger; history is never overwritten.
"""
from __future__ import annotations

import datetime
import logging
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.config import settings
from backend.app.models.submission import (
    ObservationSubmission,
    PointsLedger,
    BadgeDefinition,
    UserBadge,
    Notification,
)
from backend.app.models.user import User

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Level thresholds (points → level name)
# ─────────────────────────────────────────────────────────────────────────────

LEVELS = [
    (0,    "Trail Starter"),
    (100,  "Field Explorer"),
    (300,  "Species Specialist"),
    (600,  "Conservation Guardian"),
    (1000, "Conservation Champion"),
]


def get_level(total_points: int) -> Tuple[str, int, Optional[int]]:
    """
    Returns (level_name, current_threshold, next_threshold | None).
    """
    current_name = LEVELS[0][1]
    current_min = 0
    for i, (threshold, name) in enumerate(LEVELS):
        if total_points >= threshold:
            current_name = name
            current_min = threshold
            next_threshold = LEVELS[i + 1][0] if i + 1 < len(LEVELS) else None
        else:
            break
    return current_name, current_min, (
        next(
            (LEVELS[i + 1][0] for i, (t, _) in enumerate(LEVELS) if t == current_min and i + 1 < len(LEVELS)),
            None,
        )
    )


def user_total_points(db: Session, user_id: int) -> int:
    """Return the current total points for a user from the ledger."""
    result = db.query(func.sum(PointsLedger.amount)).filter(
        PointsLedger.user_id == user_id
    ).scalar()
    return int(result or 0)


def user_verified_count(db: Session, user_id: int) -> int:
    """Count verified submissions for a user."""
    return (
        db.query(ObservationSubmission)
        .filter(
            ObservationSubmission.researcher_id == user_id,
            ObservationSubmission.status == "VERIFIED",
        )
        .count()
    )


def user_verified_species_count(db: Session, user_id: int) -> int:
    """Count distinct species across a user's verified submissions."""
    result = (
        db.query(func.count(func.distinct(ObservationSubmission.species_id)))
        .filter(
            ObservationSubmission.researcher_id == user_id,
            ObservationSubmission.status == "VERIFIED",
        )
        .scalar()
    )
    return int(result or 0)


def user_citation_verified_count(db: Session, user_id: int) -> int:
    """Count verified submissions that have at least one citation."""
    submissions = (
        db.query(ObservationSubmission)
        .filter(
            ObservationSubmission.researcher_id == user_id,
            ObservationSubmission.status == "VERIFIED",
        )
        .all()
    )
    return sum(1 for s in submissions if s.citations and len(s.citations) > 0)


# ─────────────────────────────────────────────────────────────────────────────
# Badge seed data (called from init_db)
# ─────────────────────────────────────────────────────────────────────────────

BADGE_SEED = [
    {
        "code": "FIRST_FOOTPRINT",
        "name": "First Footprint",
        "description": "Submitted your first verified wildlife observation.",
        "icon_emoji": "🐾",
        "rule_type": "VERIFIED_COUNT",
        "rule_threshold": 1,
    },
    {
        "code": "FIELD_OBSERVER",
        "name": "Field Observer",
        "description": "Achieved 10 verified wildlife observations.",
        "icon_emoji": "🔭",
        "rule_type": "VERIFIED_COUNT",
        "rule_threshold": 10,
    },
    {
        "code": "EVIDENCE_EXPERT",
        "name": "Evidence Expert",
        "description": "Contributed 10 verified observations with supporting references.",
        "icon_emoji": "📋",
        "rule_type": "CITATION_COUNT",
        "rule_threshold": 10,
    },
    {
        "code": "CONSERVATION_CHAMPION",
        "name": "Conservation Champion",
        "description": "Achieved 50 verified wildlife observations.",
        "icon_emoji": "🏆",
        "rule_type": "VERIFIED_COUNT",
        "rule_threshold": 50,
    },
    {
        "code": "BIODIVERSITY_EXPLORER",
        "name": "Biodiversity Explorer",
        "description": "Documented verified observations of 5 distinct species.",
        "icon_emoji": "🌿",
        "rule_type": "DISTINCT_SPECIES",
        "rule_threshold": 5,
    },
]


def seed_badges(db: Session) -> None:
    """Idempotently insert badge definitions."""
    for b in BADGE_SEED:
        existing = db.query(BadgeDefinition).filter(BadgeDefinition.code == b["code"]).first()
        if not existing:
            db.add(BadgeDefinition(**b))
    db.commit()


def seed_roles(db: Session) -> None:
    """Ensure all required roles exist in the database."""
    from backend.app.models.user import Role
    required = [
        ("ADMIN",          "Platform administrator with full access"),
        ("RESEARCHER",     "Field researcher who submits wildlife sightings"),
        ("FOREST_OFFICER", "Field officer who verifies submissions"),
        ("NGO",            "NGO partner organisation user"),
        ("CITIZEN",        "Citizen science contributor"),
        ("VIEWER",         "Read-only platform viewer"),
    ]
    for name, desc in required:
        if not db.query(Role).filter(Role.name == name).first():
            db.add(Role(name=name, description=desc))
    db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Core award logic
# ─────────────────────────────────────────────────────────────────────────────

class GamificationService:

    @staticmethod
    def _add_points(
        db: Session,
        user_id: int,
        amount: int,
        reason: str,
        idempotency_key: str,
        submission_id: Optional[int] = None,
    ) -> Optional[PointsLedger]:
        """
        Award points. Returns None if the idempotency_key already exists (no duplicate).
        """
        existing = (
            db.query(PointsLedger)
            .filter(
                PointsLedger.user_id == user_id,
                PointsLedger.idempotency_key == idempotency_key,
            )
            .first()
        )
        if existing:
            return None  # already awarded

        entry = PointsLedger(
            user_id=user_id,
            submission_id=submission_id,
            amount=amount,
            reason=reason,
            idempotency_key=idempotency_key,
        )
        db.add(entry)
        db.flush()
        return entry

    @staticmethod
    def _award_badge(
        db: Session,
        user_id: int,
        badge_code: str,
        submission_id: Optional[int] = None,
    ) -> Optional[UserBadge]:
        """
        Award a badge idempotently. Returns None if already awarded.
        """
        badge = db.query(BadgeDefinition).filter(BadgeDefinition.code == badge_code).first()
        if not badge:
            return None
        existing = (
            db.query(UserBadge)
            .filter(UserBadge.user_id == user_id, UserBadge.badge_id == badge.id)
            .first()
        )
        if existing:
            return None
        ub = UserBadge(
            user_id=user_id,
            badge_id=badge.id,
            triggered_by_submission_id=submission_id,
        )
        db.add(ub)
        db.flush()
        return ub

    @staticmethod
    def _notify(
        db: Session,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        submission_id: Optional[int] = None,
        points_amount: Optional[int] = None,
        badge_code: Optional[str] = None,
    ) -> None:
        notif = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            submission_id=submission_id,
            points_amount=points_amount,
            badge_code=badge_code,
        )
        db.add(notif)

    @classmethod
    def process_verification_rewards(
        cls,
        db: Session,
        submission: ObservationSubmission,
    ) -> Dict[str, Any]:
        """
        Called once when a submission transitions to VERIFIED.
        Awards base points, optional citation bonus, optional rare-species bonus.
        Then checks and awards any newly unlocked badges.
        All operations are idempotent.
        """
        user_id = submission.researcher_id
        sub_id = submission.id
        result: Dict[str, Any] = {
            "points_awarded": [],
            "badges_awarded": [],
        }

        # ── 1. Base observation points ─────────────────────────────────────
        base_key = f"VERIFY_SUBMISSION:{sub_id}"
        entry = cls._add_points(
            db,
            user_id,
            settings.POINTS_VERIFIED_OBSERVATION,
            "Verified wildlife observation",
            base_key,
            sub_id,
        )
        if entry:
            result["points_awarded"].append(
                {"key": base_key, "amount": settings.POINTS_VERIFIED_OBSERVATION}
            )
            cls._notify(
                db, user_id,
                "POINTS_AWARDED",
                "Points Awarded",
                f"You earned {settings.POINTS_VERIFIED_OBSERVATION} points for your verified observation.",
                submission_id=sub_id,
                points_amount=settings.POINTS_VERIFIED_OBSERVATION,
            )

        # ── 2. Citation bonus ──────────────────────────────────────────────
        if submission.citations and len(submission.citations) > 0:
            cit_key = f"CITATION_BONUS:{sub_id}"
            cit_entry = cls._add_points(
                db, user_id, settings.POINTS_CITATION_BONUS,
                "Citation bonus for supporting references", cit_key, sub_id,
            )
            if cit_entry:
                result["points_awarded"].append(
                    {"key": cit_key, "amount": settings.POINTS_CITATION_BONUS}
                )

        # ── 3. Rare species bonus ──────────────────────────────────────────
        rare_categories = [c.strip() for c in settings.RARE_SPECIES_IUCN.split(",")]
        if submission.species and submission.species.iucn_category in rare_categories:
            rare_key = f"RARE_SPECIES_BONUS:{sub_id}"
            rare_entry = cls._add_points(
                db, user_id, settings.POINTS_RARE_SPECIES_BONUS,
                f"Rare species bonus ({submission.species.iucn_category})",
                rare_key, sub_id,
            )
            if rare_entry:
                result["points_awarded"].append(
                    {"key": rare_key, "amount": settings.POINTS_RARE_SPECIES_BONUS}
                )

        db.flush()

        # ── 4. Badge checks ────────────────────────────────────────────────
        verified_count = user_verified_count(db, user_id)
        citation_count = user_citation_verified_count(db, user_id)
        distinct_species = user_verified_species_count(db, user_id)

        badge_checks = [
            ("FIRST_FOOTPRINT",      verified_count >= 1),
            ("FIELD_OBSERVER",       verified_count >= 10),
            ("EVIDENCE_EXPERT",      citation_count >= 10),
            ("CONSERVATION_CHAMPION",verified_count >= 50),
            ("BIODIVERSITY_EXPLORER",distinct_species >= 5),
        ]
        for badge_code, earned in badge_checks:
            if earned:
                ub = cls._award_badge(db, user_id, badge_code, sub_id)
                if ub:
                    badge_def = db.query(BadgeDefinition).filter(
                        BadgeDefinition.code == badge_code
                    ).first()
                    result["badges_awarded"].append(badge_code)
                    cls._notify(
                        db, user_id,
                        "BADGE_EARNED",
                        f"Badge Earned: {badge_def.name if badge_def else badge_code}",
                        f"You unlocked the '{badge_def.name if badge_def else badge_code}' badge! {badge_def.description if badge_def else ''}",
                        submission_id=sub_id,
                        badge_code=badge_code,
                    )

        db.flush()
        return result

    @classmethod
    def get_researcher_profile(cls, db: Session, user_id: int) -> Dict[str, Any]:
        """Return full gamification profile for a researcher."""
        total_points = user_total_points(db, user_id)
        level_name, level_min, level_next = get_level(total_points)

        verified_count = user_verified_count(db, user_id)
        distinct_species = user_verified_species_count(db, user_id)

        user_badges = (
            db.query(UserBadge, BadgeDefinition)
            .join(BadgeDefinition, UserBadge.badge_id == BadgeDefinition.id)
            .filter(UserBadge.user_id == user_id)
            .all()
        )
        badges = [
            {
                "code": bd.code,
                "name": bd.name,
                "description": bd.description,
                "icon_emoji": bd.icon_emoji,
                "awarded_at": ub.awarded_at.isoformat(),
            }
            for ub, bd in user_badges
        ]

        submission_counts = {}
        for status in ["DRAFT", "PENDING_REVIEW", "UNDER_REVIEW", "MORE_INFO_NEEDED", "VERIFIED", "REJECTED"]:
            submission_counts[status] = (
                db.query(ObservationSubmission)
                .filter(
                    ObservationSubmission.researcher_id == user_id,
                    ObservationSubmission.status == status,
                )
                .count()
            )

        progress_to_next = None
        if level_next is not None:
            progress_to_next = round(
                (total_points - level_min) / (level_next - level_min) * 100, 1
            )

        return {
            "total_points": total_points,
            "level": level_name,
            "level_min_points": level_min,
            "next_level_points": level_next,
            "progress_to_next_pct": progress_to_next,
            "verified_count": verified_count,
            "distinct_species": distinct_species,
            "badges": badges,
            "submission_counts": submission_counts,
        }
