from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.app.dependencies import get_db, get_current_user
from backend.app.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from backend.app.services.auth_service import AuthService
from backend.app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account with role assignment.
    """
    try:
        new_user = AuthService.register_user(db, user_in)
        return new_user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate with email and password, returning a JWT bearer token.
    """
    user = AuthService.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    import datetime
    user.last_active_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    role_name = user.role.name if user.role else "VIEWER"
    token = AuthService.create_access_token(
        data={"sub": user.email, "role": role_name, "user_id": user.id}
    )
    return Token(
        access_token=token,
        token_type="bearer",
        role=role_name,
        user_id=user.id,
        full_name=user.full_name
    )


@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 standard compatible token endpoint (uses username=email).
    """
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    import datetime
    user.last_active_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    role_name = user.role.name if user.role else "VIEWER"
    token = AuthService.create_access_token(
        data={"sub": user.email, "role": role_name, "user_id": user.id}
    )
    return Token(
        access_token=token,
        token_type="bearer",
        role=role_name,
        user_id=user.id,
        full_name=user.full_name
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Retrieve profile and permissions for the currently authenticated user.
    """
    return current_user
