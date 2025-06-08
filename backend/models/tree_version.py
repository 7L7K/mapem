# backend/models/tree.py

import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, synonym

from backend.models.base import Base

logger = logging.getLogger(__name__)


class TreeVersion(Base):
    """
    One row per version of an uploaded GEDCOM tree.
    • uploaded_tree_id = FK to UploadedTree
    • tree_id alias keeps the test-suite happy
    """

    __tablename__ = "tree_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    uploaded_tree_id = Column(
        UUID(as_uuid=True),
        ForeignKey("uploaded_trees.id"),
        nullable=False,
        index=True,
    )
    tree_id = synonym("uploaded_tree_id")  # 🧪 test compatibility

    version_number = Column(Integer, nullable=False, default=1)
    diff_summary = Column(String)
    status = Column(String, default="active")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    uploaded_tree = relationship("UploadedTree", back_populates="versions", lazy="joined")
    tree_persons = relationship("TreePerson", back_populates="tree_version", cascade="all, delete-orphan")
    individuals = relationship("Individual", back_populates="tree", cascade="all, delete-orphan")
    families = relationship("Family", back_populates="tree", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="tree", cascade="all, delete-orphan")
    # relationships = relationship("TreeRelationship", back_populates="tree", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("uploaded_tree_id", "version_number", name="uq_uploaded_tree_version"),
    )

    def is_active(self):
        return self.status == "active"

    def to_debug_dict(self):
        return {k: getattr(self, k) for k in self.__table__.columns.keys()}

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "tree_id": self.tree_id,
            "version": self.version_number,
            "status": self.status,
            "diff": self.diff_summary,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return (
            f"<TreeVersion id={self.id} "
            f"upload={self.uploaded_tree_id} v{self.version_number}>"
        )
