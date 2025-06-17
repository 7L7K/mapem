# backend/models/__init__.py
"""Convenient access to all SQLAlchemy models used by the application."""

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


def verify_models():
    """Quick sanity check ensuring expected columns exist."""
    expected = {
        "locations": {"status", "source", "confidence_score"},
        "individuals": {"tree_id"},
    }
    mismatches = {}
    for table_name, expected_cols in expected.items():
        table = Base.metadata.tables.get(table_name)
        if not table:
            continue
        cols = {c.name for c in table.columns}
        missing = expected_cols - cols
        if missing:
            mismatches[table_name] = missing
    if mismatches:
        logging.warning("Model verification mismatches: %s", mismatches)
    else:
        logging.debug("All expected columns present")


if __name__ == "__main__":
    from pprint import pprint

    print("📦 Tables in Base.metadata:")
    pprint(list(Base.metadata.tables))
    verify_models()
