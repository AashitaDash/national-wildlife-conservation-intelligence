"""
Researcher Submission Router
============================
Endpoints for submitting, editing, and tracking wildlife sighting submissions.
All write endpoints require authentication. Researchers see only their own submissions.
"""
from __future__ import annotations

import datetime
import logging
import os
from typing import List, Optional

from fastapi import (
    APIRouter, Depends, HTTPException, Query, UploadFile, File, status
)
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.dependencies import get_db, get_current_active_user, require_roles
from backend.app.models.submission import (
    ObservationSubmission,
    SubmissionImage,
    Notification,
    ALLOWED_TRANSITIONS,
)
from backend.app.models.user import User
from backend.app.models.species import Species
from backend.app.models.location import Location
from backend.app.schemas.submission import (
    SubmissionCreate,
    SubmissionUpdate,
    SubmissionTransition,
    SubmissionResponse,
    SubmissionImageResponse,
    NotificationResponse,
)
from backend.app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/submissions", tags=["Researcher Submission Workflow"])

# Allowed MIME types for image uploads
_ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_response(sub: ObservationSubmission) -> SubmissionResponse:
    latest = sub.decisions[0] if sub.decisions else None
    latest_dec = None
    if latest:
        from backend.app.schemas.submission import DecisionResponse
        latest_dec = DecisionResponse(
            id=latest.id,
            submission_id=latest.submission_id,
            officer_id=latest.officer_id,
            officer_name=latest.officer.full_name if latest.officer else None,
            action=latest.action,
            note=latest.note,
            decided_at=latest.decided_at,
        )

    return SubmissionResponse(
        id=sub.id,
        researcher_id=sub.researcher_id,
        researcher_name=sub.researcher.full_name if sub.researcher else None,
        species_id=sub.species_id,
        species_common_name=sub.species.common_name if sub.species else None,
        species_scientific_name=sub.species.scientific_name if sub.species else None,
        species_iucn_category=sub.species.iucn_category if sub.species else None,
        location_id=sub.location_id,
        location_name=sub.location.name if sub.location else None,
        observed_at=sub.observed_at,
        latitude=sub.latitude,
        longitude=sub.longitude,
        accuracy_meters=sub.accuracy_meters,
        description=sub.description,
        habitat_notes=sub.habitat_notes,
        behavior_notes=sub.behavior_notes,
        identification_notes=sub.identification_notes,
        citations=sub.citations or [],
        status=sub.status,
        promoted_observation_id=sub.promoted_observation_id,
        images=[
            SubmissionImageResponse(
                id=img.id,
                submission_id=img.submission_id,
                file_path=img.file_path,
                original_filename=img.original_filename,
                mime_type=img.mime_type,
                file_size_bytes=img.file_size_bytes,
                uploaded_at=img.uploaded_at,
            )
            for img in sub.images
        ],
        latest_decision=latest_dec,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
    )


# ─────────────────────────────────────────────────────────────────────────────
# List & Create
# ─────────────────────────────────────────────────────────────────────────────

@router.get("", response_model=List[SubmissionResponse])
@router.get("/mine", response_model=List[SubmissionResponse])
def list_my_submissions(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    skip: int = 0,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List authenticated researcher's own submissions.
    ADMIN and FOREST_OFFICER may see all submissions by omitting automatic filtering
    — that is handled in the /officer endpoint.
    """
    query = db.query(ObservationSubmission).filter(
        ObservationSubmission.researcher_id == current_user.id
    )
    if status_filter:
        query = query.filter(ObservationSubmission.status == status_filter.upper())
    subs = query.order_by(ObservationSubmission.created_at.desc()).offset(skip).limit(limit).all()
    return [_build_response(s) for s in subs]


@router.post("", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_submission(
    payload: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new wildlife sighting submission (DRAFT or immediate PENDING_REVIEW).
    """
    # Validate species exists
    species = db.query(Species).filter(Species.id == payload.species_id).first()
    if not species:
        raise HTTPException(status_code=400, detail=f"Species ID {payload.species_id} not found.")

    # Validate location if provided
    if payload.location_id:
        if not db.query(Location).filter(Location.id == payload.location_id).first():
            raise HTTPException(status_code=400, detail=f"Location ID {payload.location_id} not found.")

    # Validate initial status
    initial_status = (payload.status or "DRAFT").upper()
    if initial_status not in ("DRAFT", "PENDING_REVIEW"):
        initial_status = "DRAFT"

    observed_at = payload.observed_at
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=datetime.timezone.utc)

    sub = ObservationSubmission(
        researcher_id=current_user.id,
        species_id=payload.species_id,
        location_id=payload.location_id,
        observed_at=observed_at,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy_meters=payload.accuracy_meters,
        description=payload.description,
        habitat_notes=payload.habitat_notes,
        behavior_notes=payload.behavior_notes,
        identification_notes=payload.identification_notes,
        citations=payload.citations or [],
        status=initial_status,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    AuditService.log(
        db, "SUBMISSION_CREATED",
        actor_id=current_user.id,
        entity_type="SUBMISSION",
        entity_id=sub.id,
        metadata={"status": sub.status, "species_id": sub.species_id},
    )
    db.commit()
    return _build_response(sub)


# ─────────────────────────────────────────────────────────────────────────────
# Get / Update / Delete
# ─────────────────────────────────────────────────────────────────────────────

def _get_own_submission(sub_id: int, user: User, db: Session) -> ObservationSubmission:
    sub = db.query(ObservationSubmission).filter(ObservationSubmission.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail=f"Submission {sub_id} not found.")
    role = user.role.name if user.role else ""
    if sub.researcher_id != user.id and role not in ("ADMIN", "FOREST_OFFICER"):
        raise HTTPException(status_code=403, detail="You do not own this submission.")
    return sub


@router.get("/{sub_id}", response_model=SubmissionResponse)
def get_submission(
    sub_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sub = _get_own_submission(sub_id, current_user, db)
    return _build_response(sub)


@router.put("/{sub_id}", response_model=SubmissionResponse)
def update_submission(
    sub_id: int,
    payload: SubmissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update a submission. Only DRAFT and MORE_INFO_NEEDED submissions can be edited.
    """
    sub = _get_own_submission(sub_id, current_user, db)

    if sub.status not in ("DRAFT", "MORE_INFO_NEEDED"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot edit a submission with status '{sub.status}'. Only DRAFT and MORE_INFO_NEEDED submissions can be modified.",
        )

    if payload.species_id is not None:
        if not db.query(Species).filter(Species.id == payload.species_id).first():
            raise HTTPException(status_code=400, detail=f"Species ID {payload.species_id} not found.")
        sub.species_id = payload.species_id
    if payload.location_id is not None:
        sub.location_id = payload.location_id
    if payload.observed_at is not None:
        sub.observed_at = payload.observed_at
    if payload.latitude is not None:
        sub.latitude = payload.latitude
    if payload.longitude is not None:
        sub.longitude = payload.longitude
    if payload.accuracy_meters is not None:
        sub.accuracy_meters = payload.accuracy_meters
    if payload.description is not None:
        sub.description = payload.description
    if payload.habitat_notes is not None:
        sub.habitat_notes = payload.habitat_notes
    if payload.behavior_notes is not None:
        sub.behavior_notes = payload.behavior_notes
    if payload.identification_notes is not None:
        sub.identification_notes = payload.identification_notes
    if payload.citations is not None:
        sub.citations = payload.citations

    sub.updated_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    db.refresh(sub)
    return _build_response(sub)


@router.post("/{sub_id}/transition", response_model=SubmissionResponse)
def transition_submission(
    sub_id: int,
    payload: SubmissionTransition,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Researcher-initiated state transition (e.g. DRAFT → PENDING_REVIEW).
    """
    sub = _get_own_submission(sub_id, current_user, db)
    new_status = payload.new_status.upper()

    if new_status not in ALLOWED_TRANSITIONS.get(sub.status, set()):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot transition from '{sub.status}' to '{new_status}'.",
        )

    # Only allow researcher to move to PENDING_REVIEW (officer actions handled in /officer)
    researcher_allowed = {"PENDING_REVIEW"}
    role = current_user.role.name if current_user.role else ""
    if new_status not in researcher_allowed and role not in ("ADMIN",):
        raise HTTPException(
            status_code=403,
            detail="Researchers can only submit to PENDING_REVIEW. Verification is performed by Forest Officers.",
        )

    sub.status = new_status
    sub.updated_at = datetime.datetime.now(datetime.timezone.utc)

    # Create a notification for PENDING_REVIEW
    if new_status == "PENDING_REVIEW":
        notif = Notification(
            user_id=current_user.id,
            notification_type="SUBMISSION_RECEIVED",
            title="Submission Received",
            message=f"Your submission (#{sub.id}) has been submitted for officer review.",
            submission_id=sub.id,
        )
        db.add(notif)

    AuditService.log(
        db, f"SUBMISSION_{new_status}",
        actor_id=current_user.id,
        entity_type="SUBMISSION",
        entity_id=sub.id,
        metadata={"from_status": sub.status, "to_status": new_status},
    )

    db.commit()
    db.refresh(sub)
    return _build_response(sub)


@router.post("/{sub_id}/submit", response_model=SubmissionResponse)
def submit_draft_for_review(
    sub_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Convenience endpoint for researchers to transition DRAFT or MORE_INFO_NEEDED to PENDING_REVIEW.
    """
    return transition_submission(
        sub_id=sub_id,
        payload=SubmissionTransition(new_status="PENDING_REVIEW"),
        db=db,
        current_user=current_user,
    )


@router.delete("/{sub_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_submission(
    sub_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a DRAFT submission. Cannot delete reviewed or verified submissions.
    """
    sub = _get_own_submission(sub_id, current_user, db)
    role = current_user.role.name if current_user.role else ""

    if sub.status not in ("DRAFT",) and role != "ADMIN":
        raise HTTPException(
            status_code=409,
            detail="Only DRAFT submissions can be deleted.",
        )

    AuditService.log(
        db, "SUBMISSION_DELETED",
        actor_id=current_user.id,
        entity_type="SUBMISSION",
        entity_id=sub.id,
        metadata={"status_at_deletion": sub.status},
    )
    db.delete(sub)
    db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Image upload
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{sub_id}/images", response_model=SubmissionImageResponse, status_code=201)
async def upload_image(
    sub_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Upload a photograph or evidence image for a submission.
    File is stored server-side in the configured UPLOAD_DIR.
    """
    sub = _get_own_submission(sub_id, current_user, db)

    if sub.status not in ("DRAFT", "MORE_INFO_NEEDED", "PENDING_REVIEW"):
        raise HTTPException(
            status_code=409,
            detail="Images can only be added to DRAFT, MORE_INFO_NEEDED, or PENDING_REVIEW submissions.",
        )

    if file.content_type not in _ALLOWED_MIME:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported image type '{file.content_type}'. Allowed: JPEG, PNG, WEBP, GIF.",
        )

    content = await file.read()
    if len(content) > _MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    # Sanitise filename and create safe server-side path
    import re, uuid
    safe_name = re.sub(r"[^\w.\-]", "_", file.filename or "image")[:100]
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    sub_dir = os.path.join(settings.UPLOAD_DIR, "submissions", str(sub_id))
    os.makedirs(sub_dir, exist_ok=True)
    file_path = os.path.join(sub_dir, unique_name)

    with open(file_path, "wb") as f:
        f.write(content)

    # Store relative path to keep paths portable
    relative_path = os.path.relpath(file_path, settings.UPLOAD_DIR)

    img = SubmissionImage(
        submission_id=sub.id,
        file_path=relative_path,
        original_filename=safe_name,
        mime_type=file.content_type,
        file_size_bytes=len(content),
    )
    db.add(img)
    db.commit()
    db.refresh(img)

    return SubmissionImageResponse(
        id=img.id,
        submission_id=img.submission_id,
        file_path=img.file_path,
        original_filename=img.original_filename,
        mime_type=img.mime_type,
        file_size_bytes=img.file_size_bytes,
        uploaded_at=img.uploaded_at,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Notifications
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/notifications/mine", response_model=List[NotificationResponse])
def list_my_notifications(
    unread_only: bool = False,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List the current user's in-app notifications."""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    notifs = query.order_by(Notification.created_at.desc()).limit(limit).all()
    return notifs


@router.post("/notifications/{notif_id}/read", status_code=200)
def mark_notification_read(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark a single notification as read."""
    notif = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == current_user.id,
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")
    notif.is_read = True
    db.commit()
    return {"status": "read"}


@router.post("/notifications/read-all", status_code=200)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark all notifications as read for the current user."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"status": "all_read"}
