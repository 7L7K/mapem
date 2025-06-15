# backend/models/individual_source.py
from sqlalchemy import (
    Column,
    Integer,
    Float,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin, ReprMixin
import uuid
from sqlalchemy.dialects.postgresql import UUID


class IndividualSource(Base, TimestampMixin, ReprMixin):
    __tablename__ = "individual_sources"
    __table_args__ = (
        UniqueConstraint("individual_id", "source_id", name="uq_individual_source"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    individual_id = Column(
        UUID(as_uuid=True),
        ForeignKey("individuals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id     = Column(
        Integer,
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    confidence    = Column(Float, default=1.0)

    individual = relationship("Individual", back_populates="individual_sources", lazy="joined")
    source     = relationship("Source",      back_populates="individual_sources", lazy="joined")
