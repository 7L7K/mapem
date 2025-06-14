# backend/models/alternate_name.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base, TimestampMixin, ReprMixin

class AlternateName(Base, TimestampMixin, ReprMixin):
    __tablename__ = "alternate_names"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    location_id  = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alternate_name = Column(String, nullable=False)

    location = relationship(
        "Location",
        back_populates="alternate_names",
        lazy="joined",
    )
