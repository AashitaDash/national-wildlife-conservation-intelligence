from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class SpeciesBase(BaseModel):
    scientific_name: str
    common_name: str
    kingdom: Optional[str] = "Animalia"
    phylum: Optional[str] = "Chordata"
    class_name: Optional[str] = None
    order_name: Optional[str] = None
    family: Optional[str] = None
    genus: Optional[str] = None
    iucn_category: str = "LC"
    description: Optional[str] = None
    image_url: Optional[str] = None
    image_source: Optional[str] = None
    image_license: Optional[str] = None
    image_attribution: Optional[str] = None


class SpeciesCreate(SpeciesBase):
    pass


class SpeciesUpdate(BaseModel):
    scientific_name: Optional[str] = None
    common_name: Optional[str] = None
    iucn_category: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    image_source: Optional[str] = None
    image_license: Optional[str] = None
    image_attribution: Optional[str] = None


class SpeciesResponse(SpeciesBase):
    id: int
    created_at: Optional[datetime] = None
    total_observations: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class SpeciesDetailResponse(SpeciesResponse):
    recent_risk_level: Optional[str] = None
    recent_risk_score: Optional[float] = None
    active_anomalies_count: Optional[int] = 0

class PaginatedSpeciesResponse(BaseModel):
    items: List[SpeciesResponse]
    total: int
    page: int
    page_size: int
