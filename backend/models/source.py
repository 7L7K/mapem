# backend/models/source.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin, ReprMixin
from .enums import SourceTypeEnum

class Source(Base, TimestampMixin, ReprMixin):
    __tablename__ = "sources"
    __table_args__ = (
        UniqueConstraint("document_hash", name="uq_sources_hash"),
    )

    id            = Column(Integer, primary_key=True, autoincrement=True)
    source_type   = Column(String, nullable=False, default=SourceTypeEnum.unknown)
    description   = Column(Text)
    url           = Column(String)
    document_hash = Column(String, nullable=False)
    text_content  = Column(JSON)

    individual_sources = relationship(
        "IndividualSource",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="noload" ,
    )
    event_sources = relationship(
        "EventSource",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="noload" ,
    )
