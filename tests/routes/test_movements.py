import pytest
from backend.main import create_app
from backend.db import get_engine
from backend.models import Base

@pytest.fixture(scope="module")
def test_client():
    app = create_app()
    app.config['TESTING'] = True

    # Use a fresh DB for testing (optional, depends on your setup)
    engine = get_engine()
    Base.metadata.create_all(engine)

    with app.test_client() as client:
        yield client

def test_movements_geocoded(test_client):
    # Replace this with a valid tree_id in your test DB
    test_tree_id = "a55c0019-c44a-43f5-a2f1-606912b3f3c5"

    response = test_client.get(f"/api/movements/{test_tree_id}")
    assert response.status_code == 200

    data = response.get_json()
    assert isinstance(data, list)

    # Check that at least one movement is returned
    assert len(data) > 0, "No movements returned"

    # Validate that lat/lng and other geo info exists in every movement event
    for ev in data:
        # lat/lng may be None if no location — fail if that happens
        lat = ev.get("latitude")
        lng = ev.get("longitude")

        assert lat is not None, f"Missing latitude for event id {ev.get('id')}"
        assert lng is not None, f"Missing longitude for event id {ev.get('id')}"

        # Optionally check confidence and source exist (can be None)
        assert "confidence_score" in ev
        assert "source" in ev

from backend.models.event import Event

def test_event_types_are_normalized():
    import backend.db as db
    session = db.SessionLocal()
    expected = {
        "birth", "death", "burial", "residence",
        "marriage", "divorce", "separation", "adoption",
        "baptism", "christening", "census",
        "emigration", "immigration"
    }

    result = session.query(Event.event_type).distinct().all()
    event_types = {row[0] for row in result}
    missing = expected - event_types

    assert not missing, f"Missing expected event types: {missing}"
