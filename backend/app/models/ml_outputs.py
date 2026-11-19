import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base


class MLRiskScore(Base):
    """
    Persisted output of the Machine Learning Conservation Risk Classification Engine.
    Represents an AI-assisted decision-support indicator (0-100) and priority tier.
    """
    __tablename__ = "ml_risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=False, index=True)
    region_name = Column(String(150), nullable=False, index=True)

    composite_score = Column(Float, nullable=False)  # 0.0 to 100.0
    risk_level = Column(String(20), nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL

    # Core feature inputs snapshot for explainability
    observation_frequency = Column(Float, nullable=True)
    threat_density = Column(Float, nullable=True)
    temporal_trend = Column(Float, nullable=True)  # e.g., negative value indicates decline
    feature_snapshot = Column(JSON, nullable=True)

    calculated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)

    species = relationship("Species", back_populates="risk_scores")

    def __repr__(self):
        return f"<MLRiskScore(id={self.id}, species_id={self.species_id}, region='{self.region_name}', score={self.composite_score:.1f}, level='{self.risk_level}')>"


class MLAnomaly(Base):
    """
    Spatial-temporal outliers identified by the Isolation Forest engine
    (unusual observation frequency drops, threat count spikes, or anomalous dispersal).
    """
    __tablename__ = "ml_anomalies"

    id = Column(Integer, primary_key=True, index=True)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True, index=True)

    anomaly_type = Column(String(50), nullable=False, index=True)  # OBSERVATION_DROP, INCIDENT_SURGE, SPATIAL_DISPERSAL
    anomaly_score = Column(Float, nullable=False)  # Negative values from Isolation Forest or normalized deviation
    is_anomaly = Column(Boolean, default=True, index=True)
    explanation = Column(Text, nullable=True)

    detected_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)

    # Operational lifecycle and workflow persistence
    status = Column(String(50), default="OPEN", index=True)  # OPEN, ACKNOWLEDGED, UNDER_INVESTIGATION, RESOLVED
    acknowledged = Column(Boolean, default=False, index=True)
    acknowledged_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    investigation_notes = Column(Text, nullable=True)

    species = relationship("Species", back_populates="anomalies")
    location = relationship("Location", back_populates="anomalies")
    acknowledged_by = relationship("User", foreign_keys=[acknowledged_by_id])

    def __repr__(self):
        return f"<MLAnomaly(id={self.id}, species_id={self.species_id}, type='{self.anomaly_type}', score={self.anomaly_score:.3f}, status='{self.status}')>"
