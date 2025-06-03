# backend/models/base.py
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy import inspect


Base = declarative_base()


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class ReprMixin:
    def __repr__(self) -> str:  # pragma: no cover
        pk = getattr(self, "id", None)
        return f"<{self.__class__.__name__} id={pk}>"


class UUIDMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

class SerializeMixin:
    """Adds a generic .to_dict() so legacy routes don’t blow up."""
    __abstract__ = True

    def to_dict(self):
        return {
            c.key: getattr(self, c.key)
            for c in inspect(self).mapper.column_attrs
        }
