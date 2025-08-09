# backend/models/location.py

"""SQLAlchemy model for geographic locations."""

from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    UniqueConstraint,
    CheckConstraint,
    Enum,
    Index,
)
from sqlalchemy.orm import relationship, validates
from geoalchemy2 import Geometry
from backend.models.types import GUID
import uuid
from datetime import datetime
from backend.models.base import Base, UUIDMixin
from .enums import LocationStatusEnum
from sqlalchemy import Enum as SQLEnum   # give it a short alias

class Location(Base, UUIDMixin):
    __tablename__ = "locations"
    __table_args__ = (
        UniqueConstraint("normalized_name", name="uq_locations_normalized"),
        Index("ix_locations_normalized_name", "normalized_name"),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="chk_lat_range"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="chk_lng_range"),
    )

    id               = Column(GUID(), primary_key=True, default=uuid.uuid4)
    raw_name         = Column(String, nullable=False)
    normalized_name  = Column(String, nullable=False, unique=True)
    latitude         = Column(Float, nullable=True)
    longitude        = Column(Float, nullable=True)
    confidence_score = Column(Float, default=0.0, nullable=False)
    source           = Column(String(50), default="none", nullable=False)
    status           = Column(SQLEnum(LocationStatusEnum, name="location_status_enum"), default=LocationStatusEnum.valid, nullable=False)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    geocoded_at      = Column(DateTime)
    geocoded_by      = Column(String)

    # PostGIS point geometry (WGS84)
    geom             = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)

    alternate_names = relationship(
        "AlternateName",
        back_populates="location",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    versions = relationship(
        "LocationVersion",
        back_populates="location",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    events = relationship(
        "Event",
        back_populates="location",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    residences = relationship(
        "ResidenceHistory",
        back_populates="location",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    versions = relationship(
        "LocationVersion",
        back_populates="location",
        lazy="noload",
        cascade="all, delete-orphan",
    )

    @validates("latitude", "longitude")
    def _validate_coords(self, key, value):
        if value is None:
            return None
        if key == "latitude" and not (-90 <= value <= 90):
            raise ValueError("latitude must be between -90 and 90")
        if key == "longitude" and not (-180 <= value <= 180):
            raise ValueError("longitude must be between -180 and 180")
        return value

