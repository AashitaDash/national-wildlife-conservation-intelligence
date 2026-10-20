from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Threat(Base):
    """
    Standardized conservation threat categories aligned with the IUCN Threat Classification Scheme.
    """
    __tablename__ = "threats"

    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(150), unique=True, nullable=False, index=True)
    iucn_threat_code = Column(String(50), nullable=True)  # e.g., '5.1.1', '2.1'
    severity_weight = Column(Float, default=1.0)          # Multiplier for risk scoring heuristics
    description = Column(Text, nullable=True)

    document_associations = relationship("DocumentThreat", back_populates="threat")

    def __repr__(self):
        return f"<Threat(id={self.id}, category='{self.category_name}', code='{self.iucn_threat_code}')>"
