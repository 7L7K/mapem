# backend/models/__init__.py
from .base import Base  # keep this

from .tree            import UploadedTree, TreePerson, TreeRelationship
from .tree_version    import TreeVersion  # ← moved next to other tree models

from .individual      import Individual, ResidenceHistory
from .family          import Family
from .event           import Event
from .location        import Location
from .alternate_name  import AlternateName
from .source          import Source
from .individual_source import IndividualSource
from .event_source      import EventSource
from .user_action     import UserAction
from .event import Event, event_participants

from backend.db import engine

# ── Sanity check: log all registered tables at import time
if __name__ == "__main__":
    print("📦 Models registered in Base.metadata →", list(Base.metadata.tables))
