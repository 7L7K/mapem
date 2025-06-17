import logging
import uuid

"""Individuals parsed from GEDCOM files with optional residences."""

from sqlalchemy import (
    Column,
    String,
    Date,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID

from backend.models.base import SerializeMixin, Base, TimestampMixin, ReprMixin
from backend.models.enums import GenderEnum

class Individual(Base, TimestampMixin, ReprMixin, SerializeMixin):
    __tablename__ = "individuals"
    __table_args__ = (
        Index("ix_individual_version_gedcom", "tree_id", "gedcom_id"),
    )

    # 🟣 NOW UUID! (was Integer)
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )

    tree_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tree_versions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    gedcom_id = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    gender = Column(SQLEnum(GenderEnum, name="gender_enum"), nullable=True)
    birth_date = Column(Date, nullable=True)
    death_date = Column(Date, nullable=True)
    occupation = Column(String, nullable=True, default="")

    tree = relationship(
        "TreeVersion",
        back_populates="individuals",
        lazy="joined",
    )
    events = relationship(
        "Event",
        secondary="event_participants",
        back_populates="participants",
        lazy="selectin"
    )
    tree_persons = relationship(
        "TreePerson",
        back_populates="individual",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    residences = relationship(
        "ResidenceHistory",
        back_populates="individual",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    individual_sources = relationship(
        "IndividualSource",
        back_populates="individual",
        lazy="noload",
        cascade="all, delete-orphan",
    )

    def has_name(self):
        return bool(self.first_name or self.last_name)

    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or "Unknown"

    def to_debug_dict(self):
        return {k: getattr(self, k) for k in self.__table__.columns.keys()}

    def __repr__(self):
        return f"<Individual id={self.id} gedcom_id={self.gedcom_id} first_name={self.first_name}>"

class ResidenceHistory(Base, TimestampMixin, ReprMixin):
    __tablename__ = "residence_history"
    __table_args__ = (
        Index("ix_res_history_indiv_dates", "individual_id", "start_date", "end_date"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    individual_id = Column(
        UUID(as_uuid=True),  # 🟣 NOW UUID!
        ForeignKey("individuals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    notes = Column(String, nullable=True)

    individual = relationship(
        "Individual",
        back_populates="residences",
        lazy="noload",
    )
    location = relationship(
        "Location",
        back_populates="residences",
        lazy="joined",
    )

    def __str__(self):
        return f"{self.start_date or '?'} to {self.end_date or '?'} @ loc:{self.location_id}"

    def to_debug_dict(self):
        return {k: getattr(self, k) for k in self.__table__.columns.keys()}

    def __repr__(self):
        return f"<ResidenceHistory id={self.id} individual_id={self.individual_id} notes={self.notes}>"


