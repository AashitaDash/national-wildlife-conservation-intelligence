from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime


class ObservationBase(BaseModel):
    species_id: int
    location_id: Optional[int] = None
    observed_at: datetime
    latitude: float
    longitude: float
    accuracy_meters: Optional[float] = None
    verification_status: Optional[str] = "VERIFIED"
    notes: Optional[str] = None
    raw_metadata: Optional[Dict[str, Any]] = None


class ObservationCreate(ObservationBase):
    source_name: Optional[str] = "Citizen Science Portal"


class ObservationResponse(ObservationBase):
    id: int
    source_id: int
    submitted_by_user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    species_common_name: Optional[str] = None
    species_scientific_name: Optional[str] = None
    species_image_url: Optional[str] = None
    source_name: Optional[str] = None
    location_name: Optional[str] = None

    class Config:
        from_attributes = True


class ObservationFilter(BaseModel):
    species_id: Optional[int] = None
    location_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_lat: Optional[float] = None
    max_lat: Optional[float] = None
    min_lon: Optional[float] = None
    max_lon: Optional[float] = None
    verification_status: Optional[str] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0
