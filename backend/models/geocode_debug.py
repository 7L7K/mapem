"""Persist per-attempt geocoding debug and raw I/O for reproducibility."""

from __future__ import annotations

from sqlalchemy import Column, String, Float, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from backend.models.base import Base, UUIDMixin
from backend.models.types import GUID


class GeocodeAttempt(Base, UUIDMixin):
    __tablename__ = "geocode_attempts"

    # The raw input string and optional normalized key
    raw_place = Column(String, nullable=False, index=True)
    name_norm = Column(String, nullable=True, index=True)
    admin_norm = Column(String, nullable=True)
    era_bucket = Column(String, nullable=True, index=True)

    # Provider used (nominatim|google|wikidata|geonames|gazetteer|manual|cache)
    provider = Column(String, nullable=False)

    # Final decision (if this attempt produced the winning result)
    chosen = Column(String, nullable=True)  # "yes" or null

    # Coordinates and score from this attempt (if any)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    score = Column(Float, nullable=True)

    # Free-form JSON fields capturing request/response and scoring explanation
    request_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    response_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    debug_scoring_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_geocode_attempts_raw_created", "raw_place", "created_at"),
    )


