# backend/models/location_version.py
"""Time-bounded alternative coordinates for a location."""
from sqlalchemy import (
    Column,
    Float,
    Integer,
    String,
    ForeignKey,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from backend.models.base import Base  # ✅ fixed import
from sqlalchemy.orm import relationship
import uuid

class LocationVersion(Base):
    __tablename__ = "location_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)

    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)

    valid_from = Column(Integer)  # year
    valid_to   = Column(Integer)  # year (NULL = open-ended)

    modern_equivalent = Column(String)
    source = Column(String)
    notes  = Column(JSONB)

    created_at = Column(DateTime, server_default=func.now())

    location = relationship(
        "Location",
        back_populates="versions",
        lazy="joined",
    )

