# backend/models/alternate_name.py
import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.types import GUID

from .base import Base, TimestampMixin, ReprMixin
import uuid

class AlternateName(Base, TimestampMixin, ReprMixin):
    __tablename__ = "alternate_names"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    location_id = Column(
        GUID(),
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
