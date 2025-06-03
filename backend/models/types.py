# backend/models/types.py  (new file)

import uuid
from sqlalchemy.types import CHAR, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class GUID(TypeDecorator):
    """Platform-independent GUID/UUID column.

    * PostgreSQL → uses the native UUID type (as_uuid=True)
    * Others (sqlite, mysql, …) → stores 32-char hex string
    * Accepts str **or** uuid.UUID on the Python side.
    """
    impl = PG_UUID        # so Alembic autogenerates native UUID on Postgres
    cache_ok = True       # SQLAlchemy 2.x requirement

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        # fallback: CHAR(32) to keep SQLite happy
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(str(value))
        # postgres driver understands uuid objects; others want hex
        return value if dialect.name == "postgresql" else value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
