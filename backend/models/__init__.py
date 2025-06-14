# backend/models/__init__.py

from .base            import Base
from .uploaded_tree   import UploadedTree, TreePerson, TreeRelationship
from .tree_version    import TreeVersion
from .individual      import Individual, ResidenceHistory
from .family          import Family
from .event           import Event, event_participants
from .location        import Location
from .alternate_name  import AlternateName
from .source          import Source
from .individual_source import IndividualSource
from .event_source     import EventSource
from .user_action      import UserAction
from .location_version import LocationVersion  # 👈 Add this line


import logging
from backend.db import engine


if __name__ == "__main__":
    from pprint import pprint

    print("📦 Tables in Base.metadata:")
    pprint(list(Base.metadata.tables))
