import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Species(Base):
    """
    Master species catalog representing wildlife taxonomy and baseline IUCN 3.1 red list conservation status.
    """
    __tablename__ = "species"

    id = Column(Integer, primary_key=True, index=True)
    scientific_name = Column(String(150), unique=True, nullable=False, index=True)
    common_name = Column(String(150), nullable=False, index=True)
    kingdom = Column(String(50), default="Animalia")
    phylum = Column(String(50), default="Chordata")
    class_name = Column(String(50), nullable=True)
    order_name = Column(String(50), nullable=True)
    family = Column(String(50), nullable=True)
    genus = Column(String(50), nullable=True)
    
    # Official IUCN Red List Category: LC, NT, VU, EN, CR, EW, EX, DD
    iucn_category = Column(String(10), nullable=False, default="LC", index=True)
    # IUCN Red List API v4 enrichment fields (populated by ingestion pipeline)
    iucn_sis_id = Column(Integer, nullable=True, index=True)            # IUCN SIS taxon identifier
    iucn_authority = Column(String(200), nullable=True)                  # Taxonomic authority string
    iucn_retrieved_at = Column(DateTime, nullable=True)                  # When IUCN data was last synced
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    image_source = Column(String(50), nullable=True)
    image_license = Column(String(100), nullable=True)
    image_attribution = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    observations = relationship("Observation", back_populates="species")
    document_associations = relationship("DocumentSpecies", back_populates="species")
    risk_scores = relationship("MLRiskScore", back_populates="species")
    anomalies = relationship("MLAnomaly", back_populates="species")
    alerts = relationship("ConservationAlert", back_populates="species")

    def __repr__(self):
        return f"<Species(id={self.id}, name='{self.common_name}', scientific='{self.scientific_name}', status='{self.iucn_category}')>"
