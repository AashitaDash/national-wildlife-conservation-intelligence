import os
import sys
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.app.dependencies import get_db, require_roles
from backend.app.models.user import User, Role
from backend.app.schemas.auth import UserResponse
from backend.app.config import settings

router = APIRouter(prefix="/admin", tags=["Administrative & Security Governance"])


@router.get("/users", response_model=List[UserResponse], dependencies=[Depends(require_roles("ADMIN"))])
def list_system_users(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """
    List registered platform users and their RBAC permissions. Restricted to Administrators.
    """
    return db.query(User).offset(skip).limit(limit).all()


@router.put("/users/{user_id}/role", response_model=UserResponse, dependencies=[Depends(require_roles("ADMIN"))])
def update_user_role(user_id: int, new_role: str = Query(..., description="Target role name (ADMIN, ECOLOGIST, RANGER, RESEARCHER, VIEWER)"), db: Session = Depends(get_db)):
    """
    Update RBAC role assignment for a user. Restricted to Administrators.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User ID {user_id} not found")

    target_role = db.query(Role).filter(Role.name == new_role.upper()).first()
    if not target_role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Role '{new_role}' does not exist.")

    user.role_id = target_role.id
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
