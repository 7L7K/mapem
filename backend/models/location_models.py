# backend/models/location_models.py
from typing import Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict


class LocationOut(BaseModel):
    raw_name: str
    normalized_name: str
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    confidence_score: float = Field(0.0, description="Confidence (0.0–1.0)")
    confidence_label: str = Field("", description="Label for confidence method")
    status: str = Field(..., description="Status of the location")
    source: str = Field("unknown", description="Source of the data")
    timestamp: Optional[str] = Field(None, description="ISO timestamp")
    model_config = ConfigDict(from_attributes=True)
