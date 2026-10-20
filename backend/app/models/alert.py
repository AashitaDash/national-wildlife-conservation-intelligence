import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base


class ConservationAlert(Base):
    """
    Actionable alerts generated automatically by risk thresholds,
    Isolation Forest anomaly detections, or urgent citizen sighting submissions.
    """
    __tablename__ = "conservation_alerts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    severity = Column(String(20), default="WARNING", index=True)  # INFO, WARNING, HIGH, CRITICAL
    alert_type = Column(String(50), nullable=False, index=True)   # RISK_THRESHOLD, ANOMALY_DETECTED, CITIZEN_SUBMISSION
    message = Column(Text, nullable=False)

    species_id = Column(Integer, ForeignKey("species.id"), nullable=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True, index=True)

    is_resolved = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)

    species = relationship("Species", back_populates="alerts")
    location = relationship("Location", back_populates="alerts")
    user_notifications = relationship("UserAlert", back_populates="alert", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ConservationAlert(id={self.id}, title='{self.title}', severity='{self.severity}')>"


class UserAlert(Base):
    """
    User-specific notification delivery and read status mapping.
    """
    __tablename__ = "user_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("conservation_alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime, nullable=True)

    alert = relationship("ConservationAlert", back_populates="user_notifications")
    user = relationship("User", back_populates="user_alerts")

    def __repr__(self):
        return f"<UserAlert(id={self.id}, user_id={self.user_id}, alert_id={self.alert_id}, read={self.is_read})>"
