#backend/models/event.py
import logging
from sqlalchemy import (
    Column, Integer, ForeignKey, Date, String, Index, Table
)
from sqlalchemy.orm import relationship
from .base import Base, ReprMixin
from sqlalchemy.dialects.postgresql import UUID
import uuid

 

# ─── Association Table: Event ↔ Individual ─────────────
event_participants = Table(
    "event_participants",
    Base.metadata,
    Column("event_id", ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column("individual_id", ForeignKey("individuals.id", ondelete="CASCADE"), primary_key=True),
)

class Event(Base, ReprMixin):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_tree_date", "tree_id", "date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tree_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tree_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    event_type     = Column(String, nullable=False)
    date           = Column(Date, nullable=True)
    date_precision = Column(String)
    notes          = Column(String)
    source_tag     = Column(String)
    category       = Column(String)
    location_id    = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), index=True)

    # ─── Relationships ───────────────────────────────────
    tree           = relationship("TreeVersion", back_populates="events", lazy="joined")
    location       = relationship("Location", lazy="joined")
    event_sources  = relationship("EventSource", back_populates="event", cascade="all, delete-orphan", lazy="noload")

    participants   = relationship(
        "Individual",
        secondary=event_participants,
        back_populates="events",
        lazy="selectin"
    )

    def serialize(self):
        data = {
            "id":         self.id,
            "tree_id":    self.tree_id,
            "event_type": self.event_type,
            "date":       self.date.isoformat() if self.date else None,
            "location_id": self.location_id,
            "notes":      self.notes,
            "source_tag": self.source_tag,
            "category":   self.category,
            "participant_ids": [p.id for p in self.participants]
        }
        logger.debug("Event.serialize → %s", data)
        return data
