# backend/models/location_version.py
"""Time-bounded alternative coordinates for a location."""
from sqlalchemy import (
    Column,
    Float,
    Integer,
    String,
    ForeignKey,
    DateTime,
    JSON,
)
from backend.models.types import GUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from backend.models.base import Base  # ✅ fixed import
from sqlalchemy.orm import relationship
import uuid

class LocationVersion(Base):
    __tablename__ = "location_versions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    location_id = Column(GUID(), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)

    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)

    valid_from = Column(Integer)  # year
    valid_to   = Column(Integer)  # year (NULL = open-ended)

    modern_equivalent = Column(String)
    source = Column(String)
    # Use a cross-dialect JSON type: JSON for SQLite, JSONB for PostgreSQL
    notes  = Column(JSON().with_variant(JSONB, "postgresql"))

    created_at = Column(DateTime, server_default=func.now())

    location = relationship(
        "Location",
        back_populates="versions",
        lazy="joined",
    )

