import pytest
from backend.db import SessionLocal
from sqlalchemy import text

TREE_ID = "5739d24c-ab00-437a-84c3-2f08d091315d"

@pytest.mark.db
def test_movement_events_have_coordinates():
    session = SessionLocal()
    try:
        result = session.execute(text("""
            SELECT e.id, e.event_type, l.normalized_name, l.latitude, l.longitude, l.status
            FROM events e
            JOIN locations l ON e.location_id = l.id
            WHERE e.tree_id = :tree_id
        """), {"tree_id": TREE_ID})

        rows = result.fetchall()
        bad_rows = []
        for r in rows:
            if not r.latitude or not r.longitude:
                bad_rows.append({
                    "event_id": r.id,
                    "place": r.normalized_name,
                    "status": r.status
                })

        assert len(bad_rows) == 0, f"❌ Found events without coordinates: {bad_rows}"
    finally:
        session.close()
