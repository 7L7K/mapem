# backend/models/location.py

from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    UniqueConstraint,
    CheckConstraint,
    Enum,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.models.base import Base, UUIDMixin
from .enums import SourceTypeEnum, LocationStatusEnum
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID  # ✅ needed for UUID support
import uuid  # ✅ needed for default uuid4

class Location(Base, UUIDMixin):
    __tablename__ = "locations"
    __table_args__ = (
        UniqueConstraint("normalized_name", name="uq_locations_normalized"),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="chk_lat_range"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="chk_lng_range"),
    )

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # ✅ UUID primary key
    raw_name         = Column(String, nullable=False)
    normalized_name  = Column(String, nullable=False, unique=True)
    latitude         = Column(Float, nullable=True)
    longitude        = Column(Float, nullable=True)
    confidence_score = Column(Float, default=0.0, nullable=False)
    source           = Column(String(50), default="none", nullable=False)
    status           = Column(SQLEnum(LocationStatusEnum, name="location_status_enum"), default=LocationStatusEnum.valid, nullable=False)
    created_at       = Column(DateTime, default=datetime.utcnow)
    geocoded_at      = Column(DateTime)
    geocoded_by      = Column(String)

    alternate_names = relationship(
        "AlternateName",
        back_populates="location",
        lazy="noload",
        cascade="all, delete-orphan",
    )
