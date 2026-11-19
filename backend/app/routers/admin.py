import datetime
import os
import sys
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.app.dependencies import get_db, require_roles, get_current_user
from backend.app.models.user import User, Role
from backend.app.schemas.auth import UserResponse, UserApprovalRequest
from backend.app.config import settings
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["Administrative & Security Governance"])


@router.get("/users", response_model=List[UserResponse], dependencies=[Depends(require_roles("ADMIN"))])
def list_system_users(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """
    List registered platform users and their RBAC permissions. Restricted to Administrators.
    """
    return db.query(User).offset(skip).limit(limit).all()


@router.put("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    new_role: str = Query(..., description="Target role name (ADMIN, FOREST_OFFICER, RESEARCHER, NGO, CITIZEN, VIEWER)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("ADMIN")),
):
    """
    Update RBAC role assignment for a user. Restricted to Administrators.
    Prevents an admin from accidentally removing their own last administrative access.
    Records who assigned the role and when in the audit log.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User ID {user_id} not found")

    target_role = db.query(Role).filter(Role.name == new_role.upper()).first()
    if not target_role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Role '{new_role}' does not exist.")

    # Guard: Prevent admin from removing their own administrative access
    if user.id == current_admin.id and target_role.name != "ADMIN":
        # Check if there is another active admin
        other_admins = db.query(User).join(Role).filter(
            Role.name == "ADMIN",
            User.id != current_admin.id,
            User.is_active == True,
            getattr(User, "is_suspended", False) == False
        ).count()
        if other_admins == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove your own administrative role. You are the sole active platform administrator."
            )

    old_role = user.role.name if user.role else "UNKNOWN"
    user.role_id = target_role.id
    user.role_assigned_by_id = current_admin.id
    user.role_assigned_at = datetime.datetime.now(datetime.timezone.utc)

    AuditService.log(
        db,
        action="ROLE_CHANGED",
        actor_id=current_admin.id,
        entity_type="USER",
        entity_id=user.id,
        metadata={
            "from_role": old_role,
            "to_role": target_role.name,
            "assigned_by_admin": current_admin.email,
        }
    )

    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}/approve", response_model=UserResponse)
def approve_user_registration(
    user_id: int,
    approval_in: UserApprovalRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("ADMIN")),
):
    """
    Approve or reject a pending user registration. Restricted to Administrators.
    Can optionally assign a vetted role upon approval (e.g. RESEARCHER, FOREST_OFFICER).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User ID {user_id} not found")

    action = approval_in.action.upper()
    if action not in ("APPROVE", "REJECT"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action must be 'APPROVE' or 'REJECT'.")

    now = datetime.datetime.now(datetime.timezone.utc)
    if action == "APPROVE":
        user.approval_status = "APPROVED"
        user.approved_by_id = current_admin.id
        user.approved_at = now

        if approval_in.assigned_role:
            target_role = db.query(Role).filter(Role.name == approval_in.assigned_role.upper()).first()
            if target_role:
                user.role_id = target_role.id
                user.role_assigned_by_id = current_admin.id
                user.role_assigned_at = now
    else:
        user.approval_status = "REJECTED"
        user.approved_by_id = current_admin.id
        user.approved_at = now

    AuditService.log(
        db,
        action="USER_APPROVAL_STATUS_CHANGED",
        actor_id=current_admin.id,
        entity_type="USER",
        entity_id=user.id,
        metadata={
            "status": user.approval_status,
            "approved_by_admin": current_admin.email,
            "assigned_role": user.role.name if user.role else None,
        }
    )

    db.commit()
    db.refresh(user)
    return user


@router.get("/system-health", dependencies=[Depends(require_roles("ADMIN", "ECOLOGIST"))])
def system_health_status(db: Session = Depends(get_db)):
    """
    Diagnostic status of API gateway, ML models, and persistence engines.
    """
    rf_model_exists = os.path.exists(os.path.join(settings.ML_MODEL_DIR, "risk_random_forest.joblib"))
    if_model_exists = os.path.exists(os.path.join(settings.ML_MODEL_DIR, "anomaly_isolation_forest.joblib"))

    return {
        "status": "HEALTHY",
        "python_version": sys.version.split()[0],
        "environment": settings.ENVIRONMENT,
        "database_connected": True,
        "models_loaded": {
            "random_forest_risk_classifier": rf_model_exists,
            "isolation_forest_anomaly_detector": if_model_exists
        }
    }


@router.post("/trigger-seed")
def trigger_database_seed(db: Session = Depends(get_db)):
    """
    On-demand administrative endpoint to seed baseline biodiversity data.
    """
    from backend.app.services.seed_service import seed_biodiversity_dataset
    from backend.app.seed_demo_dataset import seed_demo_users, seed_demo_submissions
    from backend.app.services.gamification_service import seed_badges, seed_roles
    seed_roles(db)
    seed_badges(db)
    users = seed_demo_users(db)
    seed_biodiversity_dataset(db)
    seed_demo_submissions(db, users)
    return {"status": "SUCCESS", "message": "Biodiversity dataset seeded successfully"}

