"""
Researcher Submission, Officer Verification, Gamification, Notifications, and Audit models.

All new models extend Base from the existing database module and integrate with the
existing User, Species, Observation, and Location models.
"""
from __future__ import annotations

import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, UniqueConstraint, Index, JSON,
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


# ──────────────────────────────────────────────────────────────────────────────
# Submission State Machine
#
#  DRAFT → PENDING_REVIEW → UNDER_REVIEW → VERIFIED
#                                        → REJECTED
#                                        → MORE_INFO_NEEDED → PENDING_REVIEW
# ──────────────────────────────────────────────────────────────────────────────

SUBMISSION_STATES = {
    "DRAFT",
    "PENDING_REVIEW",
    "UNDER_REVIEW",
    "MORE_INFO_NEEDED",
    "VERIFIED",
    "REJECTED",
}

# Allowed transitions: state → set of allowed next states
ALLOWED_TRANSITIONS = {
    "DRAFT":            {"PENDING_REVIEW"},
    "PENDING_REVIEW":   {"UNDER_REVIEW", "REJECTED"},
    "UNDER_REVIEW":     {"VERIFIED", "REJECTED", "MORE_INFO_NEEDED"},
    "MORE_INFO_NEEDED": {"PENDING_REVIEW"},
    "VERIFIED":         set(),   # terminal
    "REJECTED":         {"PENDING_REVIEW"},  # allow resubmission
}


class ObservationSubmission(Base):
    """
    Researcher-submitted wildlife sighting.
    Distinct from the imported Observation records (GBIF, iNaturalist, eBird).
    Only promoted to the trusted Observation table after officer verification.
    """
    __tablename__ = "observation_submissions"

    id = Column(Integer, primary_key=True, index=True)
    researcher_id = Column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    species_id = Column(
        Integer, ForeignKey("species.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    location_id = Column(
        Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Sighting details
    observed_at = Column(DateTime, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy_meters = Column(Float, nullable=True)

    # Narrative fields
    description = Column(Text, nullable=False)
    habitat_notes = Column(Text, nullable=True)
    behavior_notes = Column(Text, nullable=True)
    identification_notes = Column(Text, nullable=True)

    # Citations / references
    citations = Column(JSON, nullable=True)   # List[str] — DOIs, URLs, publication refs

    # Workflow state
    status = Column(String(30), default="DRAFT", nullable=False, index=True)

    # After officer verification this references the promoted observation record
    promoted_observation_id = Column(
        Integer, ForeignKey("observations.id", ondelete="SET NULL"), nullable=True
    )

    created_at = Column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    # Relationships
    researcher = relationship("User", foreign_keys=[researcher_id], backref="submissions")
    species = relationship("Species", backref="submissions")
    location = relationship("Location", backref="submissions")
    promoted_observation = relationship("Observation", foreign_keys=[promoted_observation_id])
    images = relationship(
        "SubmissionImage", back_populates="submission", cascade="all, delete-orphan"
    )
    decisions = relationship(
        "VerificationDecision", back_populates="submission", cascade="all, delete-orphan",
        order_by="VerificationDecision.decided_at.desc()",
    )

    def __repr__(self):
        return (
            f"<ObservationSubmission(id={self.id}, species_id={self.species_id}, "
            f"status='{self.status}', researcher_id={self.researcher_id})>"
        )


class SubmissionImage(Base):
    """
    Uploaded photograph or evidence image attached to a researcher submission.
    Stores a safe server-side file path; never a raw client-supplied path.
    """
    __tablename__ = "submission_images"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(
        Integer, ForeignKey("observation_submissions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    # Relative path under the configured upload directory — never client-supplied
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=True)  # sanitised original name for display
    mime_type = Column(String(100), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    uploaded_at = Column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    submission = relationship("ObservationSubmission", back_populates="images")

    def __repr__(self):
        return f"<SubmissionImage(id={self.id}, submission_id={self.submission_id})>"


class VerificationDecision(Base):
    """
    Immutable officer review record for a single submission.
    Append-only: each action creates a new row; history is never overwritten.
    """
    __tablename__ = "verification_decisions"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(
        Integer, ForeignKey("observation_submissions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    officer_id = Column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    # Action that was taken
    action = Column(
        String(30), nullable=False, index=True
    )  # VERIFY, REJECT, REQUEST_MORE_INFO, FLAG
    note = Column(Text, nullable=True)

    decided_at = Column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )

    submission = relationship("ObservationSubmission", back_populates="decisions")
    officer = relationship("User", foreign_keys=[officer_id], backref="verification_decisions")

    def __repr__(self):
        return (
            f"<VerificationDecision(id={self.id}, submission_id={self.submission_id}, "
            f"action='{self.action}', officer_id={self.officer_id})>"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Gamification
# ──────────────────────────────────────────────────────────────────────────────

class PointsLedger(Base):
    """
    Append-only contribution points ledger.
    Each award or adjustment creates a new row; historical rows are never modified.
    Idempotency is enforced by the unique (user_id, idempotency_key) constraint.
    """
    __tablename__ = "points_ledger"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Linked entity
    submission_id = Column(
        Integer, ForeignKey("observation_submissions.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    amount = Column(Integer, nullable=False)           # positive award, negative adjustment
    reason = Column(String(200), nullable=False)       # human-readable reason
    # e.g. "VERIFY_SUBMISSION:42", "CITATION_BONUS:42", "ADMIN_CORRECTION:42"
    idempotency_key = Column(String(200), nullable=False)

    awarded_at = Column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )

    user = relationship("User", foreign_keys=[user_id], backref="points_ledger")
    submission = relationship("ObservationSubmission", foreign_keys=[submission_id])

    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_points_user_idempotency"),
    )

    def __repr__(self):
        return (
            f"<PointsLedger(id={self.id}, user_id={self.user_id}, "
            f"amount={self.amount}, reason='{self.reason}')>"
        )


class BadgeDefinition(Base):
    """
    Platform badge catalog. Defines award criteria programmatically.
    """
    __tablename__ = "badge_definitions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon_emoji = Column(String(10), nullable=True)

    # Award rule: type + threshold value
    # Types: FIRST_VERIFICATION, VERIFIED_COUNT, CITATION_COUNT, DISTINCT_SPECIES, POINTS_TOTAL
    rule_type = Column(String(50), nullable=False)
    rule_threshold = Column(Integer, nullable=False, default=1)

    user_badges = relationship("UserBadge", back_populates="badge")

    def __repr__(self):
        return f"<BadgeDefinition(code='{self.code}', rule='{self.rule_type}:{self.rule_threshold}')>"


class UserBadge(Base):
    """
    Awarded badge record. Idempotency enforced by unique (user_id, badge_id).
    """
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    badge_id = Column(
        Integer, ForeignKey("badge_definitions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    awarded_at = Column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    # Submission that triggered the award
    triggered_by_submission_id = Column(
        Integer, ForeignKey("observation_submissions.id", ondelete="SET NULL"), nullable=True
    )

    user = relationship("User", foreign_keys=[user_id], backref="badges")
    badge = relationship("BadgeDefinition", back_populates="user_badges")

    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
    )

    def __repr__(self):
        return f"<UserBadge(user_id={self.user_id}, badge_id={self.badge_id})>"


# ──────────────────────────────────────────────────────────────────────────────
# Notifications & Audit
# ──────────────────────────────────────────────────────────────────────────────

class Notification(Base):
    """
    In-app notifications for submission lifecycle events, points awards, and badge unlocks.
    Separate from ConservationAlert (which is for ecological system alerts).
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Notification type: SUBMISSION_RECEIVED, UNDER_REVIEW, VERIFIED, REJECTED,
    #                    MORE_INFO_NEEDED, POINTS_AWARDED, BADGE_EARNED
    notification_type = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, index=True)

    # Optional references
    submission_id = Column(
        Integer, ForeignKey("observation_submissions.id", ondelete="SET NULL"), nullable=True
    )
    points_amount = Column(Integer, nullable=True)
    badge_code = Column(String(50), nullable=True)

    created_at = Column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )

    user = relationship("User", foreign_keys=[user_id], backref="notifications")

    def __repr__(self):
        return (
            f"<Notification(id={self.id}, user_id={self.user_id}, "
            f"type='{self.notification_type}', read={self.is_read})>"
        )


class AuditEvent(Base):
    """
    Append-only audit trail for security-sensitive platform events.
    Never updated or deleted.
    """
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action = Column(String(100), nullable=False, index=True)
    # e.g. "ROLE_CHANGE", "ACCOUNT_SUSPENDED", "SUBMISSION_CREATED",
    #       "SUBMISSION_VERIFIED", "SUBMISSION_REJECTED", "REWARD_ADJUSTMENT"
    entity_type = Column(String(50), nullable=True)   # "USER", "SUBMISSION", "OBSERVATION"
    entity_id = Column(Integer, nullable=True, index=True)
    event_metadata = Column(JSON, nullable=True)            # non-sensitive context only
    created_at = Column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )

    actor = relationship("User", foreign_keys=[actor_id], backref="audit_events_as_actor")

    def __repr__(self):
        return (
            f"<AuditEvent(id={self.id}, action='{self.action}', "
            f"entity={self.entity_type}:{self.entity_id})>"
        )
