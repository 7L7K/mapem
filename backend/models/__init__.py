# backend/models/__init__.py
from .base import Base  # keep this

from .uploaded_tree     import UploadedTree, TreePerson, TreeRelationship
from .tree_version      import TreeVersion
from .individual        import Individual, ResidenceHistory
from .family            import Family
from .event             import Event, event_participants
from .location          import Location
from .alternate_name    import AlternateName
from .source            import Source
from .individual_source import IndividualSource
from .event_source      import EventSource
from .user_action       import UserAction

import logging
from backend.db import engine

logger = logging.getLogger(__name__)

# ── Sanity check: log all registered tables at import time
if __name__ == "__main__":
    logger.info("📦 Models registered in Base.metadata → %s", list(Base.metadata.tables))
