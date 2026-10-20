"""
Authentication and RBAC unit tests.
Validates bcrypt password hashing, JWT encoding/decoding, registration, and login.
"""

import pytest
from backend.app.database import SessionLocal
from backend.app.services.auth_service import AuthService
from backend.app.schemas.auth import UserCreate
from backend.app.models.user import User, Role


def test_bcrypt_hashing_and_verification():
    password = "SuperConservationPassword2026!"
    hashed = AuthService.hash_password(password)
    
    assert hashed != password
    assert AuthService.verify_password(password, hashed) is True
    assert AuthService.verify_password("WrongPassword123", hashed) is False


def test_jwt_token_generation_and_decoding():
    data = {"sub": "ecologist@wildlife.gov.in", "role": "ECOLOGIST", "user_id": 42}
    token = AuthService.create_access_token(data)
    
    assert isinstance(token, str)
    decoded = AuthService.decode_access_token(token)
    assert decoded is not None
    assert decoded.email == "ecologist@wildlife.gov.in"
    assert decoded.role == "ECOLOGIST"
    assert decoded.user_id == 42


def test_user_registration_and_authentication():
    db = SessionLocal()
    try:
        test_email = "test_ranger_unique@wildlife.gov.in"
        # Cleanup if exists
        existing = db.query(User).filter(User.email == test_email).first()
        if existing:
            db.delete(existing)
            db.commit()

        user_in = UserCreate(
            email=test_email,
            password="RangerSecret2026!",
            full_name="Test Field Ranger",
            organization="Forest Department",
            role_name="RANGER"
        )
        new_user = AuthService.register_user(db, user_in)
        assert new_user.id is not None
        assert new_user.email == test_email
        # The system defaults unseeded or unprivileged roles to VIEWER
        assert new_user.role.name == "VIEWER"

        # Test valid login authentication
        authed = AuthService.authenticate_user(db, test_email, "RangerSecret2026!")
        assert authed is not None
        assert authed.id == new_user.id

        # Test invalid password
        failed = AuthService.authenticate_user(db, test_email, "IncorrectPassword")
        assert failed is None

    finally:
        db.close()
