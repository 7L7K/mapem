# backend/models/family.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin, ReprMixin
from .enums import FamilyTypeEnum
from sqlalchemy import Enum as SQLEnum   # give it a short alias
from backend.models.uploaded_tree import TreeRelationship
from backend.models.types import GUID
import uuid

class Family(Base, TimestampMixin, ReprMixin):
    __tablename__ = "families"
    __table_args__ = (
        Index("ix_families_version_gedcom", "tree_id", "gedcom_id"),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tree_id = Column(
        GUID(),
        ForeignKey("tree_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    gedcom_id       = Column(String, nullable=True)
    husband_id = Column(GUID(), ForeignKey("individuals.id", ondelete="SET NULL"), nullable=True)
    wife_id = Column(GUID(), ForeignKey("individuals.id", ondelete="SET NULL"), nullable=True)


    family_type     = Column(SQLEnum(FamilyTypeEnum, name="family_type_enum"), nullable=True)

    notes           = Column(Text, nullable=True)

    # Backref to version
    tree = relationship(
        "TreeVersion",
        back_populates="families",
        lazy="joined",
    )    
    husband = relationship("Individual", foreign_keys=[husband_id], lazy="joined")
    wife    = relationship("Individual", foreign_keys=[wife_id],    lazy="joined")

    children = relationship(
        "Individual",
        secondary="tree_relationships",
        primaryjoin="or_(Family.husband_id==TreeRelationship.person_id, Family.wife_id==TreeRelationship.person_id)",
        secondaryjoin="Individual.id==TreeRelationship.related_person_id",
        viewonly=True,
        lazy="noload" ,
    )
    
    @property
    def num_children(self) -> int:
        return len(self.children)

