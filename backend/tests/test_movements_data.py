import pytest
from sqlalchemy import text
from backend.db import SessionLocal

# Same TREE_ID you’re debugging
TREE_ID = "5739d24c-ab00-437a-84c3-2f08d091315d"

# Allowed event types
ALLOWED_TYPES = {"birth", "death", "marriage", "residence"}


@pytest.mark.db
def test_all_movements_have_real_coordinates():
    """
    Ensure no movement is stuck at the default center [37.8, -96].
    Also confirm latitude/longitude are non-null.
    """
    session = SessionLocal()
    try:
        result = session.execute(text("""
            SELECT
                e.id AS event_id,
                l.latitude,
                l.longitude
            FROM events e
            JOIN locations l ON e.location_id = l.id
            WHERE e.tree_id = :tree_id
        """), {"tree_id": TREE_ID})
        rows = result.fetchall()

        bad = []
        for r in rows:
            lat, lng = r.latitude, r.longitude
            # catches NULL OR stuck at exactly [37.8, -96]
            if lat is None or lng is None or (lat == 37.8 and lng == -96):
                bad.append({
                    "event_id": r.event_id,
                    "latitude": lat,
                    "longitude": lng
                })

        assert not bad, f"❌ Found movements with bad coords: {bad}"
    finally:
        session.close()


@pytest.mark.db
def test_all_movements_have_person_name():
    """
    Make sure every event has at least one linked individual with first_name & last_name.
    """
    session = SessionLocal()
    try:
        result = session.execute(text("""
            SELECT
                e.id AS event_id,
                ind.first_name,
                ind.last_name
            FROM events e
            JOIN event_participants ep ON ep.event_id = e.id
            JOIN individuals ind ON ind.id = ep.individual_id
            WHERE e.tree_id = :tree_id
        """), {"tree_id": TREE_ID})
        rows = result.fetchall()

        missing_name = []
        for r in rows:
            # If either first_name or last_name is NULL or empty, record it
            if not r.first_name or not r.last_name:
                missing_name.append({
                    "event_id": r.event_id,
                    "first_name": r.first_name,
                    "last_name": r.last_name
                })

        assert not missing_name, f"❌ Found movements missing a person name: {missing_name}"
    finally:
        session.close()


@pytest.mark.db
def test_event_types_and_dates_are_valid():
    """
    Check that event_type is allowed and date (e.date) is not NULL.
    """
    session = SessionLocal()
    try:
        result = session.execute(text("""
            SELECT
                e.id AS event_id,
                e.event_type,
                e.date
            FROM events e
            WHERE e.tree_id = :tree_id
        """), {"tree_id": TREE_ID})
        rows = result.fetchall()

        bad_type = []
        bad_date = []
        for r in rows:
            if r.event_type not in ALLOWED_TYPES:
                bad_type.append({"event_id": r.event_id, "event_type": r.event_type})
            if r.date is None:
                bad_date.append({"event_id": r.event_id, "date": r.date})

        assert not bad_type, f"❌ Found invalid event types: {bad_type}"
        assert not bad_date, f"❌ Found events without a date: {bad_date}"
    finally:
        session.close()
