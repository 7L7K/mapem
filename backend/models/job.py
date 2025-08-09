from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    Index,
    JSON,
)
from sqlalchemy.dialects.postgresql import JSONB

from backend.models.base import Base
from backend.models.types import GUID


class Job(Base):
    __tablename__ = "jobs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    task_id = Column(String, index=True, nullable=False)
    job_type = Column(String(50), nullable=False)
    status = Column(
        Enum(
            "queued",
            "started",
            "progress",
            "success",
            "failure",
            name="job_status_enum",
        ),
        nullable=False,
        default="queued",
    )
    progress = Column(Integer, nullable=False, default=0)
    params = Column(JSON().with_variant(JSONB, "postgresql"))
    result = Column(JSON().with_variant(JSONB, "postgresql"))
    error = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_jobs_type_status", "job_type", "status"),
    )


