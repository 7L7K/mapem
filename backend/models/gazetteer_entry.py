"""Gazetteer cache entries for local, era-aware geocoding.

Keyed by (name_norm, admin_norm, era_bucket) with coordinates and
alternate names. Hydrated from GeoNames / Wikidata / historical sets.
"""

from __future__ import annotations

from sqlalchemy import (
    Column,
    String,
    Float,
    Index,
    Integer,
    JSON,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.models.base import Base, UUIDMixin, TimestampMixin
from backend.models.types import GUID


class GazetteerEntry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "gazetteer_entries"

    # Normalized forms
    name_norm = Column(String, nullable=False, index=True)
    admin_norm = Column(String, nullable=True, index=True)
    era_bucket = Column(String, nullable=False, index=True)  # e.g. "1800_1890", "pre_1800", "unknown"

    # Coordinates
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Provider/source attribution
    source = Column(String, nullable=False, default="unknown")  # geonames|wikidata|historical|manual
    source_id = Column(String, nullable=True)  # upstream id if available

    # Optional administrative metadata (free-form)
    country_code = Column(String, nullable=True)
    admin1 = Column(String, nullable=True)
    admin2 = Column(String, nullable=True)

    # Alternate names and additional metadata stored as JSON
    alt_names = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    meta = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    __table_args__ = (
        # Composite index to accelerate primary lookups
        Index(
            "ix_gazetteer_name_admin_era",
            "name_norm",
            "admin_norm",
            "era_bucket",
        ),
    )


def compute_era_bucket(year: int | None) -> str:
    """Map a year into a coarse bucket for era-aware lookups.

    Buckets are intentionally coarse to keep the dataset small and improve
    cache hit rates.
    """
    if year is None:
        return "unknown"
    try:
        y = int(year)
    except Exception:
        return "unknown"
    if y < 1800:
        return "pre_1800"
    if y < 1890:
        return "1800_1890"
    if y < 1950:
        return "1890_1950"
    if y < 2000:
        return "1950_2000"
    return "2000_2025"


