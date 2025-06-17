"""Database snapshot tests.

These tests require a pre-populated database snapshot and will be skipped
unless the environment variable ``RUN_DB_SNAPSHOTS`` is set to ``1``.
"""

import os
import pytest
from sqlalchemy import text
from backend.db import SessionLocal

if os.environ.get("RUN_DB_SNAPSHOTS") != "1":
    pytest.skip(
        "Skipping DB snapshot tests; set RUN_DB_SNAPSHOTS=1 to run",
        allow_module_level=True,
    )

TREE_ID = "ae81ce29-d64f-4600-b21c-21f93c008df3"

@pytest.mark.db
def test_event_type_distribution_snapshot():
    """Snapshot check of event_type counts for Tree ID."""
    session = SessionLocal()
    try:
        result = session.execute(
            text("""
                SELECT event_type, COUNT(*) 
                FROM events 
                WHERE tree_id = :tree_id 
                GROUP BY event_type 
                ORDER BY event_type
            """),
            {"tree_id": TREE_ID}
        )
        counts = dict(result.all())

        print("\n📊 Event Type Distribution:")
        for k, v in counts.items():
            print(f"  {k:10} → {v}")

        expected = {
            "birth": 99,
            "death": 74,
            "marriage": 29,
            "burial": 9,
            "residence": 10,
        }

        for event_type, expected_count in expected.items():
            assert counts.get(event_type) == expected_count, f"{event_type} count mismatch (got {counts.get(event_type)})"

    finally:
        session.close()


@pytest.mark.db
def test_total_event_count_matches_expected():
    """Verify total number of events for the tree matches upload summary."""
    session = SessionLocal()
    try:
        result = session.execute(
            text("""
                SELECT COUNT(*) FROM events WHERE tree_id = :tree_id
            """),
            {"tree_id": TREE_ID}
        )
        total = result.scalar()
        print(f"\n🧮 Total event count for tree {TREE_ID}: {total}")
        assert total == 221, f"Expected 221 events, got {total}"

    finally:
        session.close()


@pytest.mark.db
def test_event_types_are_valid():
    """Ensure all event types used are from known list."""
    session = SessionLocal()
    try:
        result = session.execute(
            text("""
                SELECT DISTINCT event_type FROM events WHERE tree_id = :tree_id
            """),
            {"tree_id": TREE_ID}
        )
        found = {row[0] for row in result.fetchall()}
        allowed = {"birth", "death", "marriage", "residence", "burial", "census", "christening"}

        print(f"\n✅ Event types used: {found}")
        assert found.issubset(allowed), f"Invalid event types detected: {found - allowed}"

    finally:
        session.close()
