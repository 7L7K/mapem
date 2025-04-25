# tests/test_routes.py
import pytest
from backend.main import create_app
from backend.db import get_engine, Base

@pytest.fixture(scope="module")
def client():
    """
    Spins up the Flask test client with an in-memory SQLite DB
    so we can hit routes fast without touching prod data.
    """
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    # Re-create schema in SQLite
    engine = get_engine()
    Base.metadata.create_all(engine)

    with app.test_client() as c:
        yield c

def test_ping(client):
    resp = client.get("/api/ping")
    assert resp.status_code == 200
    assert resp.json == {"status": "ok"}

def test_list_trees_empty(client):
    resp = client.get("/api/trees/")
    assert resp.status_code == 200
    assert resp.json == []  # fresh DB, no trees yet
