# backend/models/event_source.py
from sqlalchemy import (
    Column,
    Integer,
    Float,
    ForeignKey,
    UniqueConstraint,
)
from backend.models.types import GUID
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin, ReprMixin
import uuid
# from sqlalchemy.dialects.postgresql import UUID  # not used; using GUID for cross-dialect


class EventSource(Base, TimestampMixin, ReprMixin):
    __tablename__ = "event_sources"
    __table_args__ = (
        UniqueConstraint("event_id", "source_id", name="uq_event_source"),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    event_id   = Column(
        GUID(),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id  = Column(
        Integer,
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    confidence = Column(Float, default=1.0)

    event  = relationship("Event",  back_populates="event_sources", lazy="joined")
    source = relationship("Source", back_populates="event_sources", lazy="joined")
