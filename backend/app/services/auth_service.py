import datetime
from typing import Optional, Dict, Any
import bcrypt
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.models.user import User, Role
from backend.app.schemas.auth import UserCreate, TokenData


class AuthService:
    """
    Cryptographic authentication, password verification, and JWT management.
    Directly invokes `bcrypt` C-bindings to guarantee Python 3.14 runtime safety.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Generates bcrypt hash with strong salt work factor. Truncates to 72 bytes per bcrypt standard.
        """
        truncated = password[:72].encode("utf-8")
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(truncated, salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Validates raw candidate password against stored bcrypt hash.
        """
        try:
            truncated = plain_password[:72].encode("utf-8")
            return bcrypt.checkpw(truncated, hashed_password.encode("utf-8"))
        except Exception:
            return False

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[datetime.timedelta] = None) -> str:
        """
        Generates signed JWT access token with user identity and RBAC role.
        """
        to_encode = data.copy()
        now = datetime.datetime.now(datetime.timezone.utc)
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + datetime.timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
            
        to_encode.update({"exp": expire, "iat": now})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> Optional[TokenData]:
        """
        Decodes and verifies JWT access token signature.
        """
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            email: str = payload.get("sub")
            role: str = payload.get("role")
            user_id: int = payload.get("user_id")
            if email is None:
                return None
            return TokenData(email=email, role=role, user_id=user_id)
        except JWTError:
            return None

    @classmethod
    def authenticate_user(cls, db: Session, email: str, password: str) -> Optional[User]:
        """
        Authenticates user by email and password.
        """
        user = db.query(User).filter(User.email == email.lower().strip()).first()
        if not user or not user.is_active:
            return None
        if not cls.verify_password(password, user.hashed_password):
            return None
        return user

    @classmethod
    def register_user(cls, db: Session, user_in: UserCreate) -> User:
        """
        Registers a new user and assigns their initial RBAC role.
        """
        existing = db.query(User).filter(User.email == user_in.email.lower().strip()).first()
        if existing:
            raise ValueError(f"User with email '{user_in.email}' already exists.")

        # Resolve role
        role_name = (user_in.role_name or "VIEWER").upper()
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            # Fallback to VIEWER or first available role
            role = db.query(Role).filter(Role.name == "VIEWER").first()
            if not role:
                role = Role(name=role_name, description=f"{role_name} Role")
                db.add(role)
                db.flush()

        hashed = cls.hash_password(user_in.password)
        new_user = User(
            email=user_in.email.lower().strip(),
            hashed_password=hashed,
            full_name=user_in.full_name,
            organization=user_in.organization,
            is_active=True,
            role_id=role.id
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
