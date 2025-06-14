# backend/models/user_action.py

from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Integer,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin, ReprMixin
from sqlalchemy import Enum as SQLEnum   # give it a short alias
from .enums import ActionTypeEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid



class UserAction(Base, TimestampMixin, ReprMixin):
    __tablename__ = "user_actions"
    __table_args__ = (
        Index("ix_user_actions_upload", "uploaded_tree_id"),
        Index("ix_user_actions_individual", "individual_id"),
        Index("ix_user_actions_event", "event_id"),
    )

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uploaded_tree_id = Column(
        UUID(as_uuid=True),
        ForeignKey("uploaded_trees.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    individual_id    = Column(
        Integer,
        ForeignKey("individuals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_id         = Column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action_type      = Column(SQLEnum(ActionTypeEnum, name="action_type_enum"), nullable=False)
    user_name        = Column(String, nullable=False)
    details          = Column(JSON, nullable=True)

    # Backrefs for rich audit queries
    uploaded_tree = relationship("UploadedTree", lazy="joined")
    individual    = relationship("Individual", lazy="joined")
    event         = relationship("Event", lazy="joined")
