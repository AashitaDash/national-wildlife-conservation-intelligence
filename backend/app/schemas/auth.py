import re
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    full_name: str
    username: Optional[str] = None
    approval_status: Optional[str] = "APPROVED"


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    approval_status: Optional[str] = None


class UserBase(BaseModel):
    email: str
    username: str
    full_name: str
    organization: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Full Name is mandatory and cannot be empty or whitespace only.")
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Full Name must be at least 2 characters.")
        if len(clean) > 150:
            raise ValueError("Full Name cannot exceed 150 characters.")
        return clean

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Username is mandatory and cannot be empty.")
        clean = v.strip()
        if len(clean) < 3 or len(clean) > 30:
            raise ValueError("Username must be between 3 and 30 characters.")
        if not re.match(r"^[a-zA-Z0-9_.-]+$", clean):
            raise ValueError("Username can only contain alphanumeric characters, dots, underscores, and hyphens.")
        return clean

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean):
            raise ValueError("Invalid email format.")
        return clean


class UserCreate(UserBase):
    password: str
    role_name: Optional[str] = None  # Ignored for public registrations to prevent privilege escalation

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v


class UserLogin(BaseModel):
    email: str  # Can be email or username
    password: str


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_suspended: Optional[bool] = False
    role_id: int
    role: Optional[RoleResponse] = None
    approval_status: str = "APPROVED"
    created_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    role_assigned_by_id: Optional[int] = None
    role_assigned_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UsernameAvailabilityResponse(BaseModel):
    username: str
    available: bool
    valid: bool
    message: str
    suggestions: List[str] = []


class UserApprovalRequest(BaseModel):
    action: str  # "APPROVE" or "REJECT"
    assigned_role: Optional[str] = None  # Optional role to grant upon approval


# ==============================================================================
# V32 Email Verification & Role Selection Schemas
# ==============================================================================

class InitiateRegistrationRequest(UserCreate):
    """Initial registration submission - triggers email verification."""
    pass


class InitiateRegistrationResponse(BaseModel):
    email: str
    message: str
    cooldown_seconds: int
    expires_in_minutes: int
    verification_token: Optional[str] = None  # Returned in development / testing mode for automated test completion
    otp_code: Optional[str] = None  # Returned in development mode for easy verification testing


class VerifyEmailRequest(BaseModel):
    email: str
    otp_code: Optional[str] = None
    verification_token: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean):
            raise ValueError("Invalid email format.")
        return clean


class VerifyEmailResponse(BaseModel):
    email: str
    verified: bool
    verified_token: str  # Signed confirmation token proving email was verified
    message: str
    available_roles: List[dict]


class ResendVerificationRequest(BaseModel):
    email: str


class ResendVerificationResponse(BaseModel):
    email: str
    message: str
    cooldown_seconds: int
    otp_code: Optional[str] = None
    verification_token: Optional[str] = None


class CompleteRegistrationRequest(BaseModel):
    email: str
    verified_token: str
    selected_account_type: str  # 'public' | 'researcher' | 'officer'

    @field_validator("selected_account_type")
    @classmethod
    def validate_account_type(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ("public", "researcher", "officer"):
            raise ValueError("Invalid account type. Allowed: 'public', 'researcher', 'officer'.")
        return clean

