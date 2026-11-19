import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.app.dependencies import get_db, get_current_user
from backend.app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    UsernameAvailabilityResponse,
    InitiateRegistrationRequest,
    InitiateRegistrationResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
    CompleteRegistrationRequest,
)
from backend.app.services.auth_service import AuthService
from backend.app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])


@router.get("/check-username", response_model=UsernameAvailabilityResponse)
def check_username(
    username: str = Query(..., min_length=1, description="Candidate username to verify for availability"),
    db: Session = Depends(get_db)
):
    """
    Real-time username availability checker.
    - Case-insensitively checks username against actual database records.
    - Generates available suggestions when the username is taken.
    - Does not expose emails, full names, or any sensitive account info.
    """
    result = AuthService.check_username_availability(db, username)
    return UsernameAvailabilityResponse(**result)


@router.post("/register/initiate", response_model=InitiateRegistrationResponse, status_code=status.HTTP_200_OK)
def initiate_registration(req: InitiateRegistrationRequest, db: Session = Depends(get_db)):
    """
    Step 1: Validate registration data and dispatch email verification code.
    Account is not activated until email is verified and role is chosen.
    """
    try:
        return AuthService.initiate_registration(db, req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/register/verify-email", response_model=VerifyEmailResponse, status_code=status.HTTP_200_OK)
def verify_email(req: VerifyEmailRequest, db: Session = Depends(get_db)):
    """
    Step 2: Validate 6-digit OTP code or verification link token.
    On success, provides signed proof allowing role selection.
    """
    try:
        return AuthService.verify_email(
            db,
            email=req.email,
            otp_code=req.otp_code,
            verification_token=req.verification_token,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/register/resend", response_model=ResendVerificationResponse, status_code=status.HTTP_200_OK)
def resend_verification(req: ResendVerificationRequest, db: Session = Depends(get_db)):
    """
    Resend verification email with cooldown rate-limiting.
    """
    try:
        return AuthService.resend_verification(db, email=req.email)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/register/complete", response_model=Token, status_code=status.HTTP_201_CREATED)
def complete_registration(req: CompleteRegistrationRequest, db: Session = Depends(get_db)):
    """
    Step 3: Finalize registration with validated role selection.
    Assigns selected non-admin role and immediately returns JWT access token for dashboard routing.
    """
    try:
        user, access_token = AuthService.complete_registration(
            db,
            email=req.email,
            verified_token=req.verified_token,
            selected_account_type=req.selected_account_type,
        )
        role_name = user.role.name if user.role else "VIEWER"
        return Token(
            access_token=access_token,
            token_type="bearer",
            role=role_name,
            user_id=user.id,
            full_name=user.full_name,
            username=user.username,
            approval_status="APPROVED",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account with secure role assignment.
    Public registrations are assigned CITIZEN with PENDING status.
    Privileged roles cannot be self-assigned.
    """
    try:
        new_user = AuthService.register_user(db, user_in)
        return new_user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate with email or username and password, returning a JWT bearer token.
    """
    user = AuthService.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user.last_active_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    role_name = user.role.name if user.role else "VIEWER"
    token = AuthService.create_access_token(
        data={
            "sub": user.email,
            "role": role_name,
            "user_id": user.id,
            "username": user.username,
            "approval_status": getattr(user, "approval_status", "APPROVED")
        }
    )
    return Token(
        access_token=token,
        token_type="bearer",
        role=role_name,
        user_id=user.id,
        full_name=user.full_name,
        username=user.username,
        approval_status=getattr(user, "approval_status", "APPROVED")
    )


@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 standard compatible token endpoint (supports email or username in username field).
    """
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user.last_active_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    role_name = user.role.name if user.role else "VIEWER"
    token = AuthService.create_access_token(
        data={
            "sub": user.email,
            "role": role_name,
            "user_id": user.id,
            "username": user.username,
            "approval_status": getattr(user, "approval_status", "APPROVED")
        }
    )
    return Token(
        access_token=token,
        token_type="bearer",
        role=role_name,
        user_id=user.id,
        full_name=user.full_name,
        username=user.username,
        approval_status=getattr(user, "approval_status", "APPROVED")
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Retrieve profile and permissions for the currently authenticated user.
    """
    return current_user

