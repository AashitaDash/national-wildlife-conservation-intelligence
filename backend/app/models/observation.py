import datetime
from sqlalchemy import UniqueConstraint
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base


class DataSource(Base):
    """
    Registry of external and internal data sources (GBIF, iNaturalist, eBird, Citizen, etc.)
    """
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    url = Column(String(255), nullable=True)
    description = Column(String(500), nullable=True)

    observations = relationship("Observation", back_populates="source")

    def __repr__(self):
        return f"<DataSource(id={self.id}, name='{self.name}')>"


class Observation(Base):
    """
    Spatially and temporally registered wildlife observation record.
    Preserves provenance across external biodiversity databases and citizen submissions.
    """
    __tablename__ = "observations"

    __table_args__ = (
        # Ensure one external record per source; protects against duplicate imports
        # Works on PostgreSQL and SQLite
        UniqueConstraint('source_id', 'external_id', name='uq_observation_source_external'),
    )

    """
    Spatially and temporally registered wildlife observation record.
    Preserves provenance across external biodiversity databases and citizen submissions.
    """
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True, index=True)
    submitted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True)

    observed_at = Column(DateTime, nullable=False, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    accuracy_meters = Column(Float, nullable=True)

    # Status: VERIFIED (from authoritative API/official), CITIZEN_PENDING, FLAGGED
    verification_status = Column(String(50), default="VERIFIED", index=True)
    notes = Column(Text, nullable=True)
    raw_metadata = Column(JSON, nullable=True)
    external_id = Column(String(200), nullable=True, index=True)  # provider‑specific identifier (e.g., GBIF occurrenceID)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    species = relationship("Species", back_populates="observations")
    location = relationship("Location", back_populates="observations")
    submitter = relationship("User", back_populates="observations_submitted")
    source = relationship("DataSource", back_populates="observations")

    def __repr__(self):
        return f"<Observation(id={self.id}, species_id={self.species_id}, lat={self.latitude}, lon={self.longitude}, status='{self.verification_status}')>"

