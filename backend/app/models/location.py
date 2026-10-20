import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Location(Base):
    """
    Geographic location representing administrative zones, protected national parks,
    wildlife sanctuaries, and tiger reserves.
    """
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=True)
    protected_area_type = Column(String(100), nullable=True)  # National Park, Wildlife Sanctuary, Tiger Reserve, etc.
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    area_sq_km = Column(Float, nullable=True)
    geometry_geojson = Column(Text, nullable=True)  # GeoJSON polygon/multipolygon string
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    observations = relationship("Observation", back_populates="location")
    anomalies = relationship("MLAnomaly", back_populates="location")
    alerts = relationship("ConservationAlert", back_populates="location")

    def __repr__(self):
        return f"<Location(id={self.id}, name='{self.name}', state='{self.state}', type='{self.protected_area_type}')>"
