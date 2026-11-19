"""
Pydantic schemas for the researcher submission workflow.
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Request schemas ────────────────────────────────────────────────────────────

class SubmissionCreate(BaseModel):
    species_id: int
    location_id: Optional[int] = None
    observed_at: datetime.datetime
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    accuracy_meters: Optional[float] = Field(None, ge=0)
    description: str = Field(..., min_length=10, max_length=5000)
    habitat_notes: Optional[str] = Field(None, max_length=2000)
    behavior_notes: Optional[str] = Field(None, max_length=2000)
    identification_notes: Optional[str] = Field(None, max_length=2000)
    citations: Optional[List[str]] = None
    status: Optional[str] = "DRAFT"   # DRAFT or PENDING_REVIEW on create

    @field_validator("observed_at")
    @classmethod
    def observed_at_not_future(cls, v: datetime.datetime) -> datetime.datetime:
        if v > datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1):
            raise ValueError("Observation date cannot be in the future.")
        return v

    @field_validator("latitude")
    @classmethod
    def lat_in_india_approx(cls, v: float) -> float:
        # Approx India bounding box with buffer
        if not (4.0 <= v <= 38.0):
            raise ValueError("Latitude must be within India's geographic bounds (~4°N–38°N).")
        return v

    @field_validator("longitude")
    @classmethod
    def lon_in_india_approx(cls, v: float) -> float:
        if not (62.0 <= v <= 100.0):
            raise ValueError("Longitude must be within India's geographic bounds (~62°E–100°E).")
        return v


class SubmissionUpdate(BaseModel):
    """Researcher can update draft/more_info_needed submissions."""
    species_id: Optional[int] = None
    location_id: Optional[int] = None
    observed_at: Optional[datetime.datetime] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    accuracy_meters: Optional[float] = Field(None, ge=0)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    habitat_notes: Optional[str] = Field(None, max_length=2000)
    behavior_notes: Optional[str] = Field(None, max_length=2000)
    identification_notes: Optional[str] = Field(None, max_length=2000)
    citations: Optional[List[str]] = None


class SubmissionTransition(BaseModel):
    """Researcher-initiated status transition (e.g. DRAFT → PENDING_REVIEW)."""
    new_status: str


# ── Image summary ──────────────────────────────────────────────────────────────

class SubmissionImageResponse(BaseModel):
    id: int
    submission_id: int
    file_path: str
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    uploaded_at: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ── Verification decision ──────────────────────────────────────────────────────

class DecisionResponse(BaseModel):
    id: int
    submission_id: int
    officer_id: int
    officer_name: Optional[str] = None
    action: str
    note: Optional[str] = None
    decided_at: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OfficerDecisionRequest(BaseModel):
    action: str = Field(
        ...,
        description="VERIFY, REJECT, REQUEST_MORE_INFO, FLAG",
        pattern="^(VERIFY|REJECT|REQUEST_MORE_INFO|FLAG)$",
    )
    note: Optional[str] = Field(None, max_length=3000)


# ── Main response ──────────────────────────────────────────────────────────────

class SubmissionResponse(BaseModel):
    id: int
    researcher_id: int
    researcher_name: Optional[str] = None
    species_id: int
    species_common_name: Optional[str] = None
    species_scientific_name: Optional[str] = None
    species_iucn_category: Optional[str] = None
    location_id: Optional[int] = None
    location_name: Optional[str] = None
    observed_at: datetime.datetime
    latitude: float
    longitude: float
    accuracy_meters: Optional[float] = None
    description: str
    habitat_notes: Optional[str] = None
    behavior_notes: Optional[str] = None
    identification_notes: Optional[str] = None
    citations: Optional[List[str]] = None
    status: str
    promoted_observation_id: Optional[int] = None
    images: List[SubmissionImageResponse] = []
    latest_decision: Optional[DecisionResponse] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ── Gamification schemas ───────────────────────────────────────────────────────

class BadgeResponse(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    icon_emoji: Optional[str] = None
    awarded_at: str


class ResearcherProfileResponse(BaseModel):
    total_points: int
    level: str
    level_min_points: int
    next_level_points: Optional[int] = None
    progress_to_next_pct: Optional[float] = None
    verified_count: int
    distinct_species: int
    badges: List[BadgeResponse] = []
    submission_counts: Dict[str, int] = {}


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    display_name: str
    verified_count: int
    total_points: int
    distinct_species: int
    badge_count: int
    level: str


# ── Notification schemas ───────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    title: str
    message: str
    is_read: bool
    submission_id: Optional[int] = None
    points_amount: Optional[int] = None
    badge_code: Optional[str] = None
    created_at: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ── Admin schemas ──────────────────────────────────────────────────────────────

class AdminUserResponse(BaseModel):
    id: int
    email: str
    username: Optional[str] = None
    full_name: str
    approval_status: Optional[str] = 'APPROVED'
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime.datetime] = None
    role_assigned_by_id: Optional[int] = None
    role_assigned_at: Optional[datetime.datetime] = None
    organization: Optional[str] = None
    is_active: bool
    is_suspended: bool
    role_name: str
    created_at: Optional[datetime.datetime] = None
    last_active_at: Optional[datetime.datetime] = None
    submission_count: int = 0
    verified_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class AdminPlatformStats(BaseModel):
    total_users: int
    total_researchers: int
    total_officers: int
    total_admins: int
    active_users_24h: int
    total_submissions: int
    pending_submissions: int
    verified_submissions: int
    rejected_submissions: int
    total_species: int
    total_observations: int
    submissions_by_status: Dict[str, int]
    registrations_last_30d: List[Dict[str, Any]] = []


class RoleUpdateRequest(BaseModel):
    new_role: Optional[str] = Field(None, pattern="^(ADMIN|RESEARCHER|FOREST_OFFICER|NGO|CITIZEN|VIEWER)$")
    role_name: Optional[str] = Field(None, pattern="^(ADMIN|RESEARCHER|FOREST_OFFICER|NGO|CITIZEN|VIEWER)$")

    @property
    def target_role(self) -> str:
        role = self.new_role or self.role_name
        if not role:
            raise ValueError("Role must be specified as 'new_role' or 'role_name'.")
        return role.upper()


class AccountStatusRequest(BaseModel):
    is_active: bool
    is_suspended: Optional[bool] = None
    reason: Optional[str] = Field(None, max_length=500)

    @property
    def computed_is_suspended(self) -> bool:
        if self.is_suspended is not None:
            return self.is_suspended
        return not self.is_active

