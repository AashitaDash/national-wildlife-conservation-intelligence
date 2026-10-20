from typing import Generator, List, Callable, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.config import settings
from backend.app.models.user import User
from backend.app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/token",
    auto_error=False
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection generator yielding an isolated SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates the Bearer JWT token and retrieves the current authenticated User.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    token_data = AuthService.decode_access_token(token)
    if token_data is None or token_data.email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    return current_user


def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Allows public or anonymous reads while resolving user context if token is present.
    """
    if not token:
        return None
    try:
        token_data = AuthService.decode_access_token(token)
        if not token_data or not token_data.email:
            return None
        return db.query(User).filter(User.email == token_data.email).first()
    except Exception:
        return None


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    """
    Role-Based Access Control (RBAC) guard factory.
    Example: Depends(require_roles("ADMIN", "ECOLOGIST"))
    """
    allowed_set = {r.upper() for r in allowed_roles}

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = current_user.role.name.upper() if current_user.role else "VIEWER"
        if user_role not in allowed_set and "ADMIN" not in user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of roles [{', '.join(allowed_roles)}]. User is '{user_role}'."
            )
        return current_user

    return role_checker
