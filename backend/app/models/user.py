import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    users = relationship("User", back_populates="role", foreign_keys="User.role_id")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    organization = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    is_suspended = Column(Boolean, default=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    # Approval and Governance fields (V31 & V32)
    approval_status = Column(String(20), default="APPROVED", nullable=False)  # APPROVED, PENDING, REJECTED
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    role_assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    role_assigned_at = Column(DateTime, nullable=True)

    # Email verification fields (V32)
    is_email_verified = Column(Boolean, default=True, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    last_active_at = Column(DateTime, nullable=True)

    role = relationship("Role", back_populates="users", foreign_keys=[role_id])
    approved_by = relationship("User", remote_side=[id], foreign_keys=[approved_by_id])
    role_assigned_by = relationship("User", remote_side=[id], foreign_keys=[role_assigned_by_id])

    observations_submitted = relationship("Observation", back_populates="submitter")
    documents_authored = relationship("Document", back_populates="author_user")
    user_alerts = relationship("UserAlert", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', role='{self.role.name if self.role else self.role_id}', status='{self.approval_status}')>"


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    otp_hash = Column(String(255), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    pending_data = Column(Text, nullable=False)  # JSON-encoded registration details
    attempts = Column(Integer, default=0, nullable=False)
    resend_count = Column(Integer, default=0, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_sent_at = Column(DateTime, nullable=False)
    consumed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

