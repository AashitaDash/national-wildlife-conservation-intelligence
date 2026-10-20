"""
Forest Officer Verification Router
===================================
Endpoints for Forest Officers to manage the verification queue, 
review evidence, and issue decisions on researcher submissions.
"""
from __future__ import annotations

import datetime
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.dependencies import get_db, require_roles
from backend.app.models.submission import (
    ObservationSubmission,
    VerificationDecision,
    Notification,
    ALLOWED_TRANSITIONS,
)
from backend.app.models.observation import Observation, DataSource
from backend.app.models.user import User
from backend.app.schemas.submission import (
    SubmissionResponse,
    OfficerDecisionRequest,
    DecisionResponse,
)
from backend.app.services.gamification_service import GamificationService
from backend.app.services.audit_service import AuditService
from backend.app.routers.submissions import _build_response

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/officer",
    tags=["Officer Verification Queue"],
    dependencies=[Depends(require_roles("FOREST_OFFICER", "ADMIN"))],
)

# ── Action → status mapping ────────────────────────────────────────────────────
ACTION_STATUS_MAP = {
    "VERIFY":            "VERIFIED",
    "REJECT":            "REJECTED",
    "REQUEST_MORE_INFO": "MORE_INFO_NEEDED",
    "FLAG":              "UNDER_REVIEW",  # Flags keep in UNDER_REVIEW for senior review
}


@router.get("/queue", response_model=List[SubmissionResponse])
def get_verification_queue(
    status_filter: Optional[str] = Query(
        "PENDING_REVIEW",
        description="Status to filter (PENDING_REVIEW, UNDER_REVIEW, VERIFIED, REJECTED, MORE_INFO_NEEDED)",
    ),
    species_class: Optional[str] = Query(None, description="Filter by taxonomic class"),
    skip: int = 0,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """
    Retrieve all submissions awaiting officer action, ordered by submission date (oldest first).
    """
    query = db.query(ObservationSubmission)
    if status_filter:
        query = query.filter(
            ObservationSubmission.status == status_filter.upper()
        )
    if species_class:
        from backend.app.models.species import Species
        query = query.join(Species, ObservationSubmission.species_id == Species.id).filter(
            Species.class_name.ilike(f"%{species_class}%")
        )

    subs = query.order_by(ObservationSubmission.created_at.asc()).offset(skip).limit(limit).all()
    return [_build_response(s) for s in subs]


@router.get("/queue/stats")
def get_queue_stats(db: Session = Depends(get_db)):
    """Summary counts by status for the officer dashboard header."""
    results = (
        db.query(
            ObservationSubmission.status,
            func.count(ObservationSubmission.id).label("count"),
        )
        .group_by(ObservationSubmission.status)
        .all()
    )
    stats = {row.status: row.count for row in results}
    return {
        "pending_review": stats.get("PENDING_REVIEW", 0),
        "under_review": stats.get("UNDER_REVIEW", 0),
        "more_info_needed": stats.get("MORE_INFO_NEEDED", 0),
        "verified": stats.get("VERIFIED", 0),
        "rejected": stats.get("REJECTED", 0),
        "total": sum(stats.values()),
    }


@router.get("/queue/{sub_id}", response_model=SubmissionResponse)
def get_submission_detail(sub_id: int, db: Session = Depends(get_db)):
    """Retrieve a single submission with full decision history."""
    sub = db.query(ObservationSubmission).filter(ObservationSubmission.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail=f"Submission {sub_id} not found.")
    return _build_response(sub)


@router.post("/queue/{sub_id}/claim", response_model=SubmissionResponse)
def claim_submission(
    sub_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FOREST_OFFICER", "ADMIN")),
):
    """
    Claim a PENDING_REVIEW submission for review (transitions to UNDER_REVIEW).
    Prevents two officers from simultaneously reviewing the same submission.
    """
    sub = db.query(ObservationSubmission).filter(ObservationSubmission.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail=f"Submission {sub_id} not found.")

    if sub.status != "PENDING_REVIEW":
        raise HTTPException(
            status_code=409,
            detail=f"Submission is in state '{sub.status}', not PENDING_REVIEW. Cannot claim.",
        )

    if sub.researcher_id == current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Conflict of interest: You cannot claim your own wildlife submission.",
        )

    sub.status = "UNDER_REVIEW"
    sub.updated_at = datetime.datetime.now(datetime.timezone.utc)

    # Record a preliminary decision (CLAIM action)
    claim_decision = VerificationDecision(
        submission_id=sub.id,
        officer_id=current_user.id,
        action="CLAIM",
        note=f"Claimed for review by Officer {current_user.full_name}",
    )
    db.add(claim_decision)

    # Notify researcher
    notif = Notification(
        user_id=sub.researcher_id,
        notification_type="UNDER_REVIEW",
        title="Submission Under Review",
        message=f"Your submission (#{sub.id}) is now being reviewed by a Forest Officer.",
        submission_id=sub.id,
    )
    db.add(notif)

    AuditService.log(
        db, "SUBMISSION_CLAIMED",
        actor_id=current_user.id,
        entity_type="SUBMISSION",
        entity_id=sub.id,
    )
    db.commit()
    db.refresh(sub)
    return _build_response(sub)


@router.post("/queue/{sub_id}/decide", response_model=SubmissionResponse)
def decide_submission(
    sub_id: int,
    payload: OfficerDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FOREST_OFFICER", "ADMIN")),
):
    """
    Record a verification decision and transition the submission state.

    - VERIFY → VERIFIED → promotes to trusted Observations table, awards points/badges
    - REJECT → REJECTED → researcher notified
    - REQUEST_MORE_INFO → MORE_INFO_NEEDED → researcher notified to update submission
    - FLAG → keeps UNDER_REVIEW for senior review
    """
    sub = db.query(ObservationSubmission).filter(ObservationSubmission.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail=f"Submission {sub_id} not found.")

    if sub.status not in ("UNDER_REVIEW", "PENDING_REVIEW"):
        raise HTTPException(
            status_code=409,
            detail=(
                f"Can only decide on UNDER_REVIEW or PENDING_REVIEW submissions. "
                f"Current status: '{sub.status}'."
            ),
        )

    # Disallow self-verification (researcher cannot verify their own submission even if officer/admin)
    if sub.researcher_id == current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Conflict of interest: You cannot review or verify your own wildlife submission.",
        )

    action = payload.action.upper()
    new_status = ACTION_STATUS_MAP.get(action)
    if not new_status:
        raise HTTPException(status_code=400, detail=f"Unknown action '{action}'.")

    # Record decision
    decision = VerificationDecision(
        submission_id=sub.id,
        officer_id=current_user.id,
        action=action,
        note=payload.note,
    )
    db.add(decision)

    # Transition state (FLAG keeps UNDER_REVIEW)
    if new_status != "UNDER_REVIEW":
        sub.status = new_status
    sub.updated_at = datetime.datetime.now(datetime.timezone.utc)

    # ── Promote to observations table on VERIFY ──────────────────────────────
    if action == "VERIFY" and not sub.promoted_observation_id:
        source = db.query(DataSource).filter(DataSource.name == "Researcher Submission").first()
        if not source:
            source = DataSource(
                name="Researcher Submission",
                description="Verified researcher sighting submitted through the platform",
            )
            db.add(source)
            db.flush()

        obs = Observation(
            species_id=sub.species_id,
            location_id=sub.location_id,
            submitted_by_user_id=sub.researcher_id,
            source_id=source.id,
            observed_at=sub.observed_at,
            latitude=sub.latitude,
            longitude=sub.longitude,
            accuracy_meters=sub.accuracy_meters,
            verification_status="VERIFIED",
            notes=sub.description,
            raw_metadata={
                "submission_id": sub.id,
                "verified_by": current_user.id,
                "citations": sub.citations or [],
            },
        )
        db.add(obs)
        db.flush()
        sub.promoted_observation_id = obs.id

        # Award gamification rewards
        rewards = GamificationService.process_verification_rewards(db, sub)
        logger.info(
            "Gamification rewards for submission %d: points=%s, badges=%s",
            sub.id,
            rewards.get("points_awarded"),
            rewards.get("badges_awarded"),
        )

    # ── Researcher notifications ──────────────────────────────────────────────
    notification_type_map = {
        "VERIFY":            ("VERIFIED",        "Observation Verified! 🎉",
                              f"Your submission (#{sub.id}) has been verified and added to the wildlife database. Points and badges may have been awarded."),
        "REJECT":            ("REJECTED",         "Submission Rejected",
                              f"Your submission (#{sub.id}) was not verified. Officer note: {payload.note or 'No note provided.'}"),
        "REQUEST_MORE_INFO": ("MORE_INFO_NEEDED", "More Information Required",
                              f"The reviewing officer needs more information for submission (#{sub.id}). Note: {payload.note or 'Please provide additional details.'}"),
        "FLAG":              ("UNDER_REVIEW",     "Submission Flagged for Senior Review",
                              f"Your submission (#{sub.id}) has been flagged for additional review."),
    }
    notif_data = notification_type_map.get(action)
    if notif_data:
        notif = Notification(
            user_id=sub.researcher_id,
            notification_type=notif_data[0],
            title=notif_data[1],
            message=notif_data[2],
            submission_id=sub.id,
        )
        db.add(notif)

    AuditService.log(
        db, f"SUBMISSION_{action}",
        actor_id=current_user.id,
        entity_type="SUBMISSION",
        entity_id=sub.id,
        metadata={
            "action": action,
            "new_status": new_status,
            "promoted_observation_id": sub.promoted_observation_id,
        },
    )
    db.commit()
    db.refresh(sub)
    return _build_response(sub)


class NoteRequest(BaseModel):
    note: Optional[str] = None
    reason: Optional[str] = None


@router.post("/queue/{sub_id}/verify", response_model=SubmissionResponse)
def verify_submission(
    sub_id: int,
    payload: Optional[NoteRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FOREST_OFFICER", "ADMIN")),
):
    note = payload.note if payload else None
    return decide_submission(
        sub_id=sub_id,
        payload=OfficerDecisionRequest(action="VERIFY", note=note),
        db=db,
        current_user=current_user,
    )


@router.post("/queue/{sub_id}/reject", response_model=SubmissionResponse)
def reject_submission(
    sub_id: int,
    payload: NoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FOREST_OFFICER", "ADMIN")),
):
    note = payload.reason or payload.note or "Evidence rejected."
    return decide_submission(
        sub_id=sub_id,
        payload=OfficerDecisionRequest(action="REJECT", note=note),
        db=db,
        current_user=current_user,
    )


@router.post("/queue/{sub_id}/request-info", response_model=SubmissionResponse)
def request_info_submission(
    sub_id: int,
    payload: NoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FOREST_OFFICER", "ADMIN")),
):
    note = payload.note or payload.reason or "More information requested."
    return decide_submission(
        sub_id=sub_id,
        payload=OfficerDecisionRequest(action="REQUEST_MORE_INFO", note=note),
        db=db,
        current_user=current_user,
    )


@router.get("/decisions/history", response_model=List[DecisionResponse])
def get_officer_decision_history(
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FOREST_OFFICER", "ADMIN")),
):
    """Retrieve the calling officer's own decision history."""
    decisions = (
        db.query(VerificationDecision)
        .filter(VerificationDecision.officer_id == current_user.id)
        .order_by(VerificationDecision.decided_at.desc())
        .limit(limit)
        .all()
    )
    return [
        DecisionResponse(
            id=d.id,
            submission_id=d.submission_id,
            officer_id=d.officer_id,
            officer_name=d.officer.full_name if d.officer else None,
            action=d.action,
            note=d.note,
            decided_at=d.decided_at,
        )
        for d in decisions
    ]
