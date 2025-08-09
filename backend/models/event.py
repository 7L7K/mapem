# backend/models/event.py
"""Event records such as births, deaths or marriages."""
import logging
import uuid
from sqlalchemy import (
    Column, ForeignKey, Date, String, Index, Table
)
from sqlalchemy.orm import relationship
from backend.models.types import GUID
from backend.utils.logger import get_file_logger
from geoalchemy2 import Geometry

from .base import Base, ReprMixin

logger = get_file_logger("events")

# ─── Association Table: Event ↔ Individual ─────────────
event_participants = Table(
    "event_participants",
    Base.metadata,
    Column(
        "event_id",
        GUID(),
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "individual_id",
        GUID(),
        ForeignKey("individuals.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

class Event(Base, ReprMixin):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_tree_date", "tree_id", "date"),
        # Geometry index created in Alembic migration using GiST
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tree_id = Column(
        GUID(),
        ForeignKey("tree_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type     = Column(String, nullable=False)
    date           = Column(Date, nullable=True)
    date_precision = Column(String)
    notes          = Column(String)
    source_tag     = Column(String)
    category       = Column(String)
    location_id    = Column(
        GUID(),
        ForeignKey("locations.id", ondelete="SET NULL"),
        index=True,
    )

    # Optional denormalized geometry for fast spatial queries (copied from Location)
    geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)

    # ─── Relationships ───────────────────────────────────
    tree           = relationship("TreeVersion", back_populates="events", lazy="joined")
    location       = relationship("Location", back_populates="events", lazy="joined")
    event_sources  = relationship("EventSource", back_populates="event", cascade="all, delete-orphan", lazy="noload")

    participants   = relationship(
        "Individual",
        secondary=event_participants,
        back_populates="events",
        lazy="selectin",
    )

    def serialize(self):
        data = {
            "id":         str(self.id),
            "tree_id":    str(self.tree_id),
            "event_type": self.event_type,
            "date":       self.date.isoformat() if self.date else None,
            "location_id": str(self.location_id) if self.location_id else None,
            "notes":      self.notes,
            "source_tag": self.source_tag,
            "category":   self.category,
            "participant_ids": [str(p.id) for p in self.participants],
        }
        logger.debug("Event.serialize → %s", data)
        return data

