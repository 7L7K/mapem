import pytest
from sqlalchemy import text
from backend.db import SessionLocal

@pytest.mark.db
def test_event_type_distribution_snapshot():
    """Snapshot-style check to verify GEDCOM event coverage."""
    session = SessionLocal()
    try:
        result = session.execute(
            text("SELECT event_type, COUNT(*) FROM events GROUP BY event_type ORDER BY event_type")
        )
        counts = dict(result.all())

        print("\n📊 Event Type Distribution:")
        for k, v in counts.items():
            print(f"  {k:10} → {v}")

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
