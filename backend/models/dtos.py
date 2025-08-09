# backend/models/dtos.py
from __future__ import annotations

from typing import Optional, Tuple
from uuid import UUID
from pydantic import BaseModel, Field, ValidationError, field_validator


class MapQueryDTO(BaseModel):
    year: int = Field(..., ge=0, le=3000)
    bbox: Optional[str] = Field(None, description="xmin,ymin,xmax,ymax (lng,lat order)")
    version: UUID = Field(..., description="TreeVersion.id UUID")

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        parts = [p.strip() for p in v.split(",")]
        if len(parts) != 4:
            raise ValueError("bbox must have 4 comma-separated numbers: xmin,ymin,xmax,ymax")
        try:
            floats = list(map(float, parts))
        except ValueError:
            raise ValueError("bbox values must be numbers")
        x_min, y_min, x_max, y_max = floats
        if x_min >= x_max or y_min >= y_max:
            raise ValueError("bbox min must be less than max for both axes")
        return ",".join(parts)

    def bbox_tuple(self) -> Optional[Tuple[float, float, float, float]]:
        if not self.bbox:
            return None
        x_min, y_min, x_max, y_max = map(float, self.bbox.split(","))
        return x_min, y_min, x_max, y_max


class IndividualsQueryDTO(BaseModel):
    query: Optional[str] = Field(None, description="Name search string")
    version: UUID = Field(..., description="TreeVersion.id UUID")
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=500)


class GeocodeRetryDTO(BaseModel):
    place_id: int = Field(..., ge=1)