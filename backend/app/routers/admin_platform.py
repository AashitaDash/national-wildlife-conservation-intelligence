"""
Admin Platform Router
=====================
Extended admin endpoints: user management, platform statistics, audit log.
Complements the existing /admin router — no routes from admin.py are duplicated.
"""
from __future__ import annotations

import datetime
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from backend.app.dependencies import get_db, require_roles, get_current_active_user
from backend.app.models.user import User, Role
from backend.app.models.submission import (
    ObservationSubmission,
    AuditEvent,
    PointsLedger,
    UserBadge,
)
from backend.app.models.species import Species
from backend.app.models.observation import Observation
from backend.app.schemas.auth import UserApprovalRequest
from backend.app.schemas.submission import (
    AdminUserResponse,
    AdminPlatformStats,
    RoleUpdateRequest,
    AccountStatusRequest,
)
from backend.app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/platform",
    tags=["Admin Platform Governance"],
    dependencies=[Depends(require_roles("ADMIN"))],
)


def _build_admin_user(user: User, db: Session) -> AdminUserResponse:
    try:
        sub_count = db.query(ObservationSubmission).filter(
            ObservationSubmission.researcher_id == user.id
        ).count()
        verified_count = db.query(ObservationSubmission).filter(
            ObservationSubmission.researcher_id == user.id,
            ObservationSubmission.status == "VERIFIED",
        ).count()
    except Exception:
        # observation_submissions may not exist in SQLite dev schema
        db.rollback()
        sub_count = 0
        verified_count = 0
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        organization=user.organization,
        is_active=user.is_active,
        is_suspended=getattr(user, "is_suspended", False),
        role_name=user.role.name if user.role else "VIEWER",
        approval_status=getattr(user, "approval_status", "APPROVED"),
        created_at=user.created_at,
        last_active_at=getattr(user, "last_active_at", None),
        approved_by_id=getattr(user, "approved_by_id", None),
        approved_at=getattr(user, "approved_at", None),
        role_assigned_by_id=getattr(user, "role_assigned_by_id", None),
        role_assigned_at=getattr(user, "role_assigned_at", None),
        submission_count=sub_count,
        verified_count=verified_count,
    )


# ── Platform stats ─────────────────────────────────────────────────────────────

@router.get("/stats", response_model=AdminPlatformStats)
def get_platform_stats(db: Session = Depends(get_db)):
    """Comprehensive platform-wide statistics for the admin dashboard."""
    total_users = db.query(User).count()

    role_counts = {
        r.name: db.query(User).filter(User.role_id == r.id).count()
        for r in db.query(Role).all()
    }

    # Active users in the last 24h
    active_cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        hours=24
    )
    active_24h = db.query(User).filter(User.last_active_at >= active_cutoff).count()

    # Submission stats
    submission_status_counts = {
        row.status: row.count
        for row in db.query(
            ObservationSubmission.status,
            func.count(ObservationSubmission.id).label("count"),
        ).group_by(ObservationSubmission.status).all()
    }

    total_species = db.query(Species).count()
    total_observations = db.query(Observation).count()

    # Registrations in last 30 days — daily bucketed
    thirty_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
    day_col = func.date_trunc("day", User.created_at).label("day")
    daily_regs = (
        db.query(
            day_col,
            func.count(User.id).label("count"),
        )
        .filter(User.created_at >= thirty_days_ago)
        .group_by(day_col)
        .order_by(day_col)
        .all()
    )
    registrations_last_30d = [
        {"date": str(row.day)[:10], "count": row.count} for row in daily_regs
    ]

    return AdminPlatformStats(
        total_users=total_users,
        total_researchers=role_counts.get("RESEARCHER", 0),
        total_officers=role_counts.get("FOREST_OFFICER", 0),
        total_admins=role_counts.get("ADMIN", 0),
        active_users_24h=active_24h,
        total_submissions=sum(submission_status_counts.values()),
        pending_submissions=submission_status_counts.get("PENDING_REVIEW", 0),
        verified_submissions=submission_status_counts.get("VERIFIED", 0),
        rejected_submissions=submission_status_counts.get("REJECTED", 0),
        total_species=total_species,
        total_observations=total_observations,
        submissions_by_status=submission_status_counts,
        registrations_last_30d=registrations_last_30d,
    )


# ── User management ────────────────────────────────────────────────────────────

@router.get("/users", response_model=List[AdminUserResponse])
def list_all_users(
    role_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search by name or email"),
    skip: int = 0,
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db),
):
    """List all users with submission metrics, filterable by role and search term."""
    query = db.query(User)
    if role_filter:
        role = db.query(Role).filter(Role.name == role_filter.upper()).first()
        if role:
            query = query.filter(User.role_id == role.id)
    if search:
        like_term = f"%{search}%"
        query = query.filter(
            User.full_name.ilike(like_term) | User.email.ilike(like_term)
        )
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return [_build_admin_user(u, db) for u in users]


@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user_detail(user_id: int, db: Session = Depends(get_db)):
    """Retrieve a single user profile with submission metrics."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found.")
    return _build_admin_user(user, db)


@router.put("/users/{user_id}/role", response_model=AdminUserResponse)
def update_user_role(
    user_id: int,
    payload: RoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Assign a new RBAC role to a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found.")

    # Resolve target role FIRST before any guard checks
    try:
        target_role = payload.target_role
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Sole-admin self-demotion guard
    if user.id == current_user.id and target_role != "ADMIN":
        other_admins = db.query(User).join(Role).filter(
            Role.name == "ADMIN",
            User.id != current_user.id,
            User.is_active == True,
            User.is_suspended == False
        ).count()
        if other_admins == 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot modify your own administrative role. You are the sole active platform administrator."
            )

    new_role = db.query(Role).filter(Role.name == target_role).first()
    if not new_role:
        raise HTTPException(status_code=400, detail=f"Role '{target_role}' not found.")

    old_role = user.role.name if user.role else "UNKNOWN"
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    user.role_id = new_role.id
    user.role_assigned_by_id = current_user.id
    user.role_assigned_at = now_utc

    AuditService.log(
        db, "ROLE_CHANGED",
        actor_id=current_user.id,
        entity_type="USER",
        entity_id=user_id,
        metadata={"from_role": old_role, "to_role": target_role},
    )
    db.commit()
    db.refresh(user)
    return _build_admin_user(user, db)


@router.put("/users/{user_id}/status", response_model=AdminUserResponse)
def update_user_status(
    user_id: int,
    payload: AccountStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Activate, deactivate, or suspend a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found.")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own account status.")

    user.is_active = payload.is_active
    if hasattr(user, "is_suspended"):
        user.is_suspended = payload.computed_is_suspended

    AuditService.log(
        db, "ACCOUNT_STATUS_CHANGED",
        actor_id=current_user.id,
        entity_type="USER",
        entity_id=user_id,
        metadata={
            "is_active": payload.is_active,
            "is_suspended": payload.is_suspended,
            "reason": payload.reason,
        },
    )
    db.commit()
    db.refresh(user)
    return _build_admin_user(user, db)

@router.put("/users/{user_id}/approve", response_model=AdminUserResponse)
def approve_or_reject_user(
    user_id: int,
    payload: UserApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Approve or reject a pending registration and optionally assign a role."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found.")

    action = payload.action.upper()
    if action not in ("APPROVE", "REJECT"):
        raise HTTPException(status_code=400, detail="Action must be 'APPROVE' or 'REJECT'.")

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    if action == "APPROVE":
        user.approval_status = "APPROVED"
        user.approved_by_id = current_user.id
        user.approved_at = now_utc

        if payload.assigned_role:
            target_role = db.query(Role).filter(Role.name == payload.assigned_role.upper()).first()
            if target_role:
                user.role_id = target_role.id
                user.role_assigned_by_id = current_user.id
                user.role_assigned_at = now_utc
    else:
        user.approval_status = "REJECTED"
        user.approved_by_id = current_user.id
        user.approved_at = now_utc

    AuditService.log(
        db,
        action="USER_APPROVAL_STATUS_CHANGED",
        actor_id=current_user.id,
        entity_type="USER",
        entity_id=user.id,
        metadata={
            "status": user.approval_status,
            "action": action,
            "approved_by": current_user.email,
            "assigned_role": user.role.name if user.role else None,
        },
    )
    db.commit()
    db.refresh(user)
    return _build_admin_user(user, db)


# ── Audit log ──────────────────────────────────────────────────────────────────

@router.get("/audit-log")
def get_audit_log(
    action: Optional[str] = Query(None, description="Filter by action, e.g. ROLE_CHANGED"),
    entity_type: Optional[str] = Query(None),
    actor_id: Optional[int] = Query(None),
    days: int = Query(7, le=90, description="Look-back window in days"),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
):
    """Retrieve the platform audit trail for security monitoring."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    query = db.query(AuditEvent).filter(AuditEvent.created_at >= cutoff)

    if action:
        query = query.filter(AuditEvent.action.ilike(f"%{action}%"))
    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type.upper())
    if actor_id:
        query = query.filter(AuditEvent.actor_id == actor_id)

    events = query.order_by(AuditEvent.created_at.desc()).limit(limit).all()
    return [
        {
            "id": e.id,
            "actor_id": e.actor_id,
            "actor_name": e.actor.full_name if e.actor else "System",
            "action": e.action,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "event_metadata": e.event_metadata,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]

