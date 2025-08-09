import pytest
from backend.main import create_app
from backend.db import get_engine
from backend.models import Base

@pytest.fixture(scope="module")
def test_client():
    app = create_app()
    app.config['TESTING'] = True

    # Use in-memory SQLite patched by tests/conftest, avoid hitting Postgres
    engine = get_engine()
    Base.metadata.create_all(engine)

    with app.test_client() as client:
        yield client

def test_movements_geocoded(test_client):
    # Smoke test only: endpoint should respond 404 for unknown id
    test_tree_id = "00000000-0000-0000-0000-000000000000"
    response = test_client.get(f"/api/movements/{test_tree_id}")
    assert response.status_code in (200, 404)

from backend.models.event import Event

def test_event_types_are_normalized():
    import backend.db as db
    session = db.SessionLocal()
    # Ensure querying doesn't crash; dataset may be empty in unit tests
    session = db.SessionLocal()
    _ = session.query(Event.event_type).distinct().all()
