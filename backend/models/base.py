# backend/models/base.py
from datetime import datetime, date
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer
from backend.models.types import GUID
from sqlalchemy.orm import declarative_base
from sqlalchemy import inspect
import uuid


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
    id = Column(GUID(), primary_key=True, default=uuid4)

class SerializeMixin:
    """Adds a generic .to_dict() so legacy routes don’t blow up."""
    __abstract__ = True

    def to_dict(self):
        def _serialize_value(value):
            if isinstance(value, uuid.UUID):
                return str(value)
            if isinstance(value, (datetime, date)):
                return value.isoformat()
            return value

        return {
            c.key: _serialize_value(getattr(self, c.key))
            for c in inspect(self).mapper.column_attrs
        }

    # Backwards-compatible alias used by some routes
    def serialize(self) -> dict:
        return self.to_dict()
