from datetime import datetime, timezone
import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.types import GUID

from .base import Base, TimestampMixin, ReprMixin

class UploadedTree(Base, TimestampMixin, ReprMixin):
    __tablename__ = "uploaded_trees"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tree_name = Column(String, nullable=False)
    uploader_name = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    versions = relationship("TreeVersion", back_populates="uploaded_tree", cascade="all, delete-orphan", lazy="noload")
    tree_persons = relationship("TreePerson", back_populates="uploaded_tree", cascade="all, delete-orphan", lazy="noload")
    relationships = relationship("TreeRelationship", back_populates="tree", cascade="all, delete-orphan", lazy="noload")

    def __repr__(self):
        return f"<UploadedTree id={self.id} name={self.tree_name!r}>"


class TreePerson(Base, TimestampMixin, ReprMixin):
    __tablename__ = "tree_persons"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    uploaded_tree_id = Column(GUID(), ForeignKey("uploaded_trees.id", ondelete="CASCADE"), nullable=False, index=True)
    tree_version_id = Column(GUID(), ForeignKey("tree_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    individual_id = Column(
        GUID(),  # 🟣 UUID FK!
        ForeignKey("individuals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    uploaded_tree = relationship("UploadedTree", back_populates="tree_persons", lazy="joined")
    tree_version = relationship("TreeVersion", back_populates="tree_persons", lazy="joined")
    individual = relationship("Individual", back_populates="tree_persons", lazy="joined")

    def __repr__(self):
        return f"<TreePerson id={self.id} version={self.tree_version_id} person={self.individual_id}>"


class TreeRelationship(Base, TimestampMixin, ReprMixin):
    __tablename__ = "tree_relationships"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tree_id = Column(GUID(), ForeignKey("uploaded_trees.id", ondelete="CASCADE"), nullable=False, index=True)
    person_id = Column(GUID(), ForeignKey("individuals.id", ondelete="CASCADE"), nullable=False, index=True)
    related_person_id = Column(GUID(), ForeignKey("individuals.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String, nullable=False)
    notes = Column(String)

    tree = relationship("UploadedTree", back_populates="relationships", lazy="joined")

    def __repr__(self):
        return (
            f"<TreeRelationship version={self.tree_id} "
            f"{self.person_id} → {self.related_person_id} ({self.relationship_type})>"
        )
