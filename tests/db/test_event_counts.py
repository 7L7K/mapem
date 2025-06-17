"""Database snapshot tests.

These tests require a pre-populated database snapshot and will be skipped
unless the environment variable ``RUN_DB_SNAPSHOTS`` is set to ``1``.
"""

import os
import pytest
from sqlalchemy import text
import backend.db as db

if os.environ.get("RUN_DB_SNAPSHOTS") != "1":
    pytest.skip(
        "Skipping DB snapshot tests; set RUN_DB_SNAPSHOTS=1 to run",
        allow_module_level=True,
    )

@pytest.mark.db
def test_event_type_distribution_snapshot():
    """Snapshot-style check to verify GEDCOM event coverage."""
    session = db.SessionLocal()
    try:
        result = session.execute(
            text("SELECT event_type, COUNT(*) FROM events GROUP BY event_type ORDER BY event_type")
        )
        counts = dict(result.all())


        expected = {
            "birth": 643,
            "death": 341,
            "marriage": 110,
            "burial": 14,
            "residence": 124,
        }

        for event_type, expected_count in expected.items():
            actual = counts.get(event_type)
            assert actual == expected_count, f"{event_type} count mismatch: expected {expected_count}, got {actual}"

    finally:
        session.close()
