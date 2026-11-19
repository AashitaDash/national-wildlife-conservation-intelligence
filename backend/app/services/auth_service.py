import datetime
import re
import secrets
import json
import hashlib
from typing import Optional, Dict, Any, List, Tuple
import bcrypt
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.config import settings
from backend.app.models.user import User, Role, EmailVerificationToken
from backend.app.schemas.auth import (
    UserCreate,
    TokenData,
    InitiateRegistrationResponse,
    VerifyEmailResponse,
    ResendVerificationResponse,
)
from backend.app.services.email_service import EmailService


class AuthService:
    """
    Cryptographic authentication, password verification, JWT management,
    username availability, and secure role assignment governance.
    Directly invokes `bcrypt` C-bindings to guarantee runtime safety.
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
            username: Optional[str] = payload.get("username")
            approval_status: Optional[str] = payload.get("approval_status", "APPROVED")
            if email is None:
                return None
            return TokenData(
                email=email,
                role=role,
                user_id=user_id,
                username=username,
                approval_status=approval_status
            )
        except JWTError:
            return None

    @classmethod
    def authenticate_user(cls, db: Session, identifier: str, password: str) -> Optional[User]:
        """
        Authenticates user by email OR username and password.
        Case-insensitive lookup for both email and username.
        """
        clean_ident = identifier.strip().lower()
        user = db.query(User).filter(
            (func.lower(User.email) == clean_ident) | (func.lower(User.username) == clean_ident)
        ).first()

        if not user or not user.is_active:
            return None
        if getattr(user, "is_suspended", False):
            return None
        if not cls.verify_password(password, user.hashed_password):
            return None
        return user

    @classmethod
    def validate_username_format(cls, username: str) -> Tuple[bool, str]:
        """
        Validates allowed characters and length for a username.
        Length: 3 to 30 characters.
        Characters: letters, numbers, underscores, dots, hyphens.
        """
        if not username or not username.strip():
            return False, "Username is required."
        u = username.strip()
        if len(u) < 3:
            return False, "Username must be at least 3 characters long."
        if len(u) > 30:
            return False, "Username cannot exceed 30 characters."
        if not re.match(r"^[a-zA-Z0-9_.-]+$", u):
            return False, "Username may only contain letters, numbers, underscores, periods, and hyphens."
        return True, ""

    @classmethod
    def check_username_availability(cls, db: Session, username: str) -> Dict[str, Any]:
        """
        Checks username availability against the actual database (case-insensitively).
        If taken, generates truly available alternatives verified against the database.
        Never exposes user emails, full names, or account IDs.
        """
        is_valid, msg = cls.validate_username_format(username)
        if not is_valid:
            return {
                "username": username,
                "available": False,
                "valid": False,
                "message": msg,
                "suggestions": []
            }

        clean = username.strip().lower()
        existing = db.query(User.id).filter(func.lower(User.username) == clean).first()

        if existing is None:
            return {
                "username": username,
                "available": True,
                "valid": True,
                "message": "Username is available",
                "suggestions": []
            }

        # Username is taken: Generate real alternatives and check them against DB
        suggestions = cls.generate_available_suggestions(db, clean)
        return {
            "username": username,
            "available": False,
            "valid": True,
            "message": "Username is already taken",
            "suggestions": suggestions
        }

    @classmethod
    def generate_available_suggestions(cls, db: Session, base_username: str, count: int = 3) -> List[str]:
        """
        Generates alternative candidate usernames based on the entered username,
        verifying each candidate against the actual database to ensure genuine availability.
        """
        base = re.sub(r"[^a-zA-Z0-9]", "", base_username)[:20]
        if not base:
            base = "user"

        candidates = [
            f"{base}_{datetime.datetime.now().year}",
            f"{base}_wildlife",
            f"{base}_field",
            f"{base}_ranger",
            f"{base}_bio",
            f"{base}01",
            f"{base}07",
            f"{base}42",
            f"{base}99",
            f"{base}101",
            f"eco_{base}",
            f"res_{base}",
        ]

        verified_available: List[str] = []
        for candidate in candidates:
            cand_lower = candidate.lower()
            exists = db.query(User.id).filter(func.lower(User.username) == cand_lower).first()
            if not exists and cand_lower not in [s.lower() for s in verified_available]:
                verified_available.append(candidate)
                if len(verified_available) >= count:
                    break

        return verified_available

    @classmethod
    def register_user(cls, db: Session, user_in: UserCreate) -> User:
        """
        Registers a new user with secure role assignment and mandatory full name.
        CRITICAL SECURITY REQUIREMENT:
        - Public registrations are strictly assigned CITIZEN (or VIEWER fallback) with PENDING approval status.
        - Public user payloads specifying privileged roles (ADMIN, FOREST_OFFICER, RESEARCHER) are strictly overridden/ignored.
        - Usernames are case-insensitively unique.
        """
        clean_email = user_in.email.lower().strip()
        clean_username = user_in.username.strip()
        clean_full_name = user_in.full_name.strip()

        if not clean_full_name:
            raise ValueError("Full Name is mandatory and cannot be empty or whitespace.")

        is_valid_uname, uname_err = cls.validate_username_format(clean_username)
        if not is_valid_uname:
            raise ValueError(uname_err)

        # Check existing email
        existing_email = db.query(User).filter(func.lower(User.email) == clean_email).first()
        if existing_email:
            raise ValueError(f"An account with email '{user_in.email}' already exists.")

        # Check existing username (case-insensitive)
        existing_username = db.query(User).filter(func.lower(User.username) == clean_username.lower()).first()
        if existing_username:
            raise ValueError(f"Username '{user_in.username}' is already taken.")

        # Resolve safe public registration role (CITIZEN or VIEWER)
        # Never allow public user payload to assign ADMIN, FOREST_OFFICER, or RESEARCHER
        safe_role = db.query(Role).filter(Role.name == "CITIZEN").first()
        if not safe_role:
            safe_role = db.query(Role).filter(Role.name == "VIEWER").first()
        if not safe_role:
            safe_role = Role(name="CITIZEN", description="Citizen science contributor")
            db.add(safe_role)
            db.flush()

        hashed = cls.hash_password(user_in.password)
        now = datetime.datetime.now(datetime.timezone.utc)

        new_user = User(
            username=clean_username,
            email=clean_email,
            hashed_password=hashed,
            full_name=clean_full_name,
            organization=user_in.organization.strip() if user_in.organization else None,
            is_active=True,
            is_suspended=False,
            role_id=safe_role.id,
            approval_status="PENDING",  # Awaiting admin approval for elevated privileges
            created_at=now,
            last_active_at=None,
        )
    # ==========================================================================
    # V32 Email Verification & Self-Service Role Assignment Methods
    # ==========================================================================

    ROLE_DESCRIPTIONS = [
        {
            "id": "public",
            "title": "General Public",
            "target_role": "CITIZEN",
            "description": "For citizens, wildlife enthusiasts, and naturalists. Report field sightings, explore public biodiversity intelligence, track regional conservation alerts, and participate in community monitoring.",
        },
        {
            "id": "researcher",
            "title": "Researcher",
            "target_role": "RESEARCHER",
            "description": "For academic researchers, biologists, and ecologists. Access advanced research datasets, submit scientific field observation dossiers with citations, and review NLP threat extractions.",
        },
        {
            "id": "officer",
            "title": "Forest / Wildlife Officer",
            "target_role": "FOREST_OFFICER",
            "description": "For forest rangers, field officers, and sanctuary enforcement personnel. Access the Officer Desk, patrol monitoring telemetry, incident response queues, and spatial risk indices.",
        },
    ]

    @classmethod
    def _hash_token(cls, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def initiate_registration(cls, db: Session, user_in: UserCreate) -> InitiateRegistrationResponse:
        """
        Validates initial registration inputs and generates an email verification OTP and secure link token.
        Does NOT create the permanent User account yet.
        """
        clean_email = user_in.email.lower().strip()
        clean_username = user_in.username.strip()
        clean_full_name = user_in.full_name.strip()

        if not clean_full_name:
            raise ValueError("Full Name is mandatory and cannot be empty or whitespace.")

        is_valid_uname, uname_err = cls.validate_username_format(clean_username)
        if not is_valid_uname:
            raise ValueError(uname_err)

        # Check existing email
        existing_email = db.query(User).filter(func.lower(User.email) == clean_email).first()
        if existing_email:
            raise ValueError(f"An account with email '{user_in.email}' already exists.")

        # Check existing username (case-insensitive)
        existing_username = db.query(User).filter(func.lower(User.username) == clean_username.lower()).first()
        if existing_username:
            raise ValueError(f"Username '{user_in.username}' is already taken.")

        now = datetime.datetime.now(datetime.timezone.utc)

        # Check rate-limiting on previous active token for this email
        prev_token = (
            db.query(EmailVerificationToken)
            .filter(
                EmailVerificationToken.email == clean_email,
                EmailVerificationToken.consumed_at.is_(None),
                EmailVerificationToken.expires_at > now,
            )
            .order_by(EmailVerificationToken.created_at.desc())
            .first()
        )

        if prev_token:
            # Check cooldown
            elapsed = (now - prev_token.last_sent_at.replace(tzinfo=datetime.timezone.utc)).total_seconds() if prev_token.last_sent_at.tzinfo else (now - prev_token.last_sent_at).total_seconds()
            if elapsed < settings.EMAIL_RESEND_COOLDOWN_SECONDS:
                remaining = int(settings.EMAIL_RESEND_COOLDOWN_SECONDS - elapsed)
                raise ValueError(f"Please wait {remaining} seconds before requesting a new verification code.")

        # Invalidate any older unconsumed tokens for this email
        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.email == clean_email,
            EmailVerificationToken.consumed_at.is_(None),
        ).update({"consumed_at": now})

        # Generate 6-digit OTP and secure link token
        otp = f"{secrets.randbelow(900000) + 100000:06d}"
        raw_token = secrets.token_urlsafe(32)
        otp_hash = cls.hash_password(otp)
        token_hash = cls._hash_token(raw_token)

        expires_at = now + datetime.timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRY_MINUTES)

        # Securely prepare pending payload
        hashed_pwd = cls.hash_password(user_in.password)
        pending_data = {
            "username": clean_username,
            "email": clean_email,
            "full_name": clean_full_name,
            "organization": user_in.organization.strip() if user_in.organization else None,
            "hashed_password": hashed_pwd,
        }

        token_record = EmailVerificationToken(
            email=clean_email,
            otp_hash=otp_hash,
            token_hash=token_hash,
            pending_data=json.dumps(pending_data),
            attempts=0,
            resend_count=0,
            expires_at=expires_at,
            last_sent_at=now,
            consumed_at=None,
        )
        db.add(token_record)
        db.commit()

        # Send verification email via EmailService
        verification_link = f"/register?step=verify&token={raw_token}&email={clean_email}"
        EmailService.send_verification_email(
            to_email=clean_email,
            full_name=clean_full_name,
            otp=otp,
            verification_link=verification_link,
        )

        return InitiateRegistrationResponse(
            email=clean_email,
            message="Verification code sent to your registered email address.",
            cooldown_seconds=settings.EMAIL_RESEND_COOLDOWN_SECONDS,
            expires_in_minutes=settings.EMAIL_VERIFICATION_EXPIRY_MINUTES,
            verification_token=raw_token,
            otp_code=otp,
        )

    @classmethod
    def resend_verification(cls, db: Session, email: str) -> ResendVerificationResponse:
        """
        Resends verification OTP with strict rate limiting.
        """
        clean_email = email.lower().strip()
        now = datetime.datetime.now(datetime.timezone.utc)

        token_record = (
            db.query(EmailVerificationToken)
            .filter(
                EmailVerificationToken.email == clean_email,
                EmailVerificationToken.consumed_at.is_(None),
            )
            .order_by(EmailVerificationToken.created_at.desc())
            .first()
        )

        if not token_record:
            raise ValueError("No active registration found for this email. Please register first.")

        if token_record.resend_count >= settings.MAX_RESEND_ATTEMPTS:
            raise ValueError("Maximum resend attempts reached. Please start a new registration.")

        last_sent = token_record.last_sent_at
        if last_sent.tzinfo is None:
            last_sent = last_sent.replace(tzinfo=datetime.timezone.utc)
        elapsed = (now - last_sent).total_seconds()
        if elapsed < settings.EMAIL_RESEND_COOLDOWN_SECONDS:
            remaining = int(settings.EMAIL_RESEND_COOLDOWN_SECONDS - elapsed)
            raise ValueError(f"Please wait {remaining} seconds before requesting a new code.")

        # Generate fresh OTP and update
        new_otp = f"{secrets.randbelow(900000) + 100000:06d}"
        new_raw_token = secrets.token_urlsafe(32)
        token_record.otp_hash = cls.hash_password(new_otp)
        token_record.token_hash = cls._hash_token(new_raw_token)
        token_record.resend_count += 1
        token_record.last_sent_at = now
        token_record.expires_at = now + datetime.timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRY_MINUTES)
        db.commit()

        # Parse pending user data to get full name
        pending = json.loads(token_record.pending_data)
        EmailService.send_verification_email(
            to_email=clean_email,
            full_name=pending.get("full_name", "User"),
            otp=new_otp,
            verification_link=f"/register?step=verify&token={new_raw_token}&email={clean_email}",
        )

        return ResendVerificationResponse(
            email=clean_email,
            message="A fresh verification code has been dispatched.",
            cooldown_seconds=settings.EMAIL_RESEND_COOLDOWN_SECONDS,
            otp_code=new_otp,
            verification_token=new_raw_token,
        )

    @classmethod
    def verify_email(
        cls,
        db: Session,
        email: str,
        otp_code: Optional[str] = None,
        verification_token: Optional[str] = None,
    ) -> VerifyEmailResponse:
        """
        Validates OTP code or secure link token against the stored hash.
        Enforces single-use, max attempts, and expiration.
        On success, returns a signed proof token allowing account type selection.
        """
        clean_email = email.lower().strip()
        now = datetime.datetime.now(datetime.timezone.utc)

        token_record = (
            db.query(EmailVerificationToken)
            .filter(
                EmailVerificationToken.email == clean_email,
                EmailVerificationToken.consumed_at.is_(None),
            )
            .order_by(EmailVerificationToken.created_at.desc())
            .first()
        )

        if not token_record:
            raise ValueError("No active verification request found. Please request a new code.")

        expires = token_record.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=datetime.timezone.utc)
        if now > expires:
            raise ValueError("Verification code has expired. Please request a new one.")

        if token_record.attempts >= settings.MAX_VERIFY_ATTEMPTS:
            token_record.consumed_at = now
            db.commit()
            raise ValueError("Too many failed attempts. This verification code has been invalidated.")

        # Check verification mode
        match = False
        if verification_token:
            cand_hash = cls._hash_token(verification_token)
            if cand_hash == token_record.token_hash:
                match = True
        elif otp_code:
            clean_otp = otp_code.strip()
            if cls.verify_password(clean_otp, token_record.otp_hash):
                match = True

        if not match:
            token_record.attempts += 1
            db.commit()
            remaining_attempts = max(0, settings.MAX_VERIFY_ATTEMPTS - token_record.attempts)
            raise ValueError(f"Invalid verification code. {remaining_attempts} attempts remaining.")

        # Match succeeded! Mark token as consumed (one-time use)
        token_record.consumed_at = now
        db.commit()

        # Generate a signed verified_token carrying email and pending data hash
        pending = json.loads(token_record.pending_data)
        verified_token_payload = {
            "sub": clean_email,
            "type": "email_verified",
            "username": pending["username"],
            "full_name": pending["full_name"],
            "organization": pending.get("organization"),
            "hashed_password": pending["hashed_password"],
            "exp": now + datetime.timedelta(minutes=30),  # 30 mins to choose role
        }
        signed_proof = jwt.encode(verified_token_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        return VerifyEmailResponse(
            email=clean_email,
            verified=True,
            verified_token=signed_proof,
            message="Email verified successfully. Please choose your platform role to complete setup.",
            available_roles=cls.ROLE_DESCRIPTIONS,
        )

    @classmethod
    def complete_registration(
        cls,
        db: Session,
        email: str,
        verified_token: str,
        selected_account_type: str,
    ) -> Tuple[User, str]:
        """
        Completes registration:
        - Validates the cryptographic verified_token.
        - Validates role selection against allowed non-admin roles:
            - 'public'     -> CITIZEN
            - 'researcher' -> RESEARCHER
            - 'officer'    -> FOREST_OFFICER
        - Administrator is NEVER allowed through this endpoint.
        - Persists the User record with is_email_verified=True, is_active=True, approval_status='APPROVED'.
        - Generates and returns an immediate JWT token for seamless dashboard access.
        """
        clean_email = email.lower().strip()
        account_type = selected_account_type.lower().strip()

        # 1. Decode & verify proof token
        try:
            payload = jwt.decode(verified_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            if payload.get("type") != "email_verified" or payload.get("sub") != clean_email:
                raise ValueError("Invalid verification token for this email address.")
        except JWTError:
            raise ValueError("Verification token has expired or is invalid. Please verify email again.")

        # 2. Prevent duplicate user check
        existing = db.query(User).filter(func.lower(User.email) == clean_email).first()
        if existing:
            raise ValueError(f"An account with email '{clean_email}' already exists.")

        username = payload.get("username")
        existing_uname = db.query(User).filter(func.lower(User.username) == username.lower()).first()
        if existing_uname:
            raise ValueError(f"Username '{username}' has already been registered.")

        # 3. Map selected_account_type to safe non-admin DB Role
        role_map = {
            "public": "CITIZEN",
            "researcher": "RESEARCHER",
            "officer": "FOREST_OFFICER",
        }

        if account_type not in role_map:
            raise ValueError(f"Invalid account type '{selected_account_type}'. Must be public, researcher, or officer.")

        target_role_name = role_map[account_type]

        # Enforce that ADMIN cannot ever be assigned here
        if target_role_name == "ADMIN":
            raise ValueError("Unauthorized role assignment: Administrator accounts cannot be self-selected.")

        # Fetch or initialize role
        db_role = db.query(Role).filter(Role.name == target_role_name).first()
        if not db_role:
            if target_role_name == "CITIZEN":
                db_role = db.query(Role).filter(Role.name == "VIEWER").first()
            if not db_role:
                db_role = Role(name=target_role_name, description=f"Registered as {account_type}")
                db.add(db_role)
                db.flush()

        now = datetime.datetime.now(datetime.timezone.utc)

        # 4. Create permanent user
        new_user = User(
            username=username,
            email=clean_email,
            hashed_password=payload.get("hashed_password"),
            full_name=payload.get("full_name"),
            organization=payload.get("organization"),
            is_active=True,
            is_suspended=False,
            role_id=db_role.id,
            approval_status="APPROVED",  # Self-service activated upon email verification
            is_email_verified=True,
            email_verified_at=now,
            created_at=now,
            last_active_at=now,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # 5. Generate immediate JWT token for automated routing
        token = cls.create_access_token(
            data={
                "sub": new_user.email,
                "role": db_role.name,
                "user_id": new_user.id,
                "username": new_user.username,
                "approval_status": "APPROVED",
            }
        )

        return new_user, token

