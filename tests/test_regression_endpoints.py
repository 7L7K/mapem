import logging
import pytest
import time
from flask import Flask
from backend.main import create_app
from backend.db import get_db
from backend.models import TreeVersion

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


# ─── fixtures ─────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def app():
    app = create_app()
    app.config.update(TESTING=True)
    return app


@pytest.fixture(scope="module")
def client(app: Flask):
    return app.test_client()


@pytest.fixture(scope="module")
def tree_ids():
    db = next(get_db())
    latest = db.query(TreeVersion).order_by(TreeVersion.created_at.desc()).first()
    if not latest:
        raise RuntimeError("No trees in DB – upload one first.")
    return {
        "tree_version_id": latest.id,
        "uploaded_tree_id": latest.uploaded_tree_id,
    }


# ─── helper ───────────────────────────────────────────────────────────
def timed_get(client, url):
    start = time.time()
    res = client.get(url)
    logging.getLogger(__name__).info(
        "%s -> %s in %.2f s",
        url,
        res.status_code,
        round(time.time() - start, 2),
    )
    return res


# ─── regression checks ────────────────────────────────────────────────
def test_basic_counts(client, tree_ids):
    tree_version_id = tree_ids["tree_version_id"]
    res = timed_get(client, f"/api/trees/{tree_version_id}/counts")
    data = res.get_json()
    assert res.status_code in (200, 404)
    assert {"individuals", "families"} <= data.keys()


def test_movements(client, tree_ids):
    uploaded_tree_id = tree_ids["uploaded_tree_id"]
    res = timed_get(client, f"/api/movements/{uploaded_tree_id}")
    data = res.get_json()
    assert res.status_code == 200
    assert isinstance(data, list)
    if data:
        assert "event_id" in data[0]


def test_events(client, tree_ids):
    version_id = tree_ids["tree_version_id"]
    res = timed_get(client, f"/api/events/?version_id={version_id}")
    data = res.get_json()
    assert res.status_code == 200
    assert isinstance(data, list)


def test_people(client, tree_ids):
    uploaded_tree_id = tree_ids["uploaded_tree_id"]
    res  = timed_get(client, f"/api/people/{uploaded_tree_id}")
    data = res.get_json()
    assert res.status_code == 200
    assert isinstance(data["people"], list)


def test_schema(client, tree_ids):
    uploaded_tree_id = tree_ids["uploaded_tree_id"]
    res  = timed_get(client, f"/api/schema/{uploaded_tree_id}")
    data = res.get_json()
    assert res.status_code == 200
    assert {"individuals", "events"} <= data.keys()


def test_visible_counts_endpoint(client, tree_ids):
    uploaded_tree_id = tree_ids["uploaded_tree_id"]
    params = {
        "person": "",
        "yearRange": [1800, 1950],
        "eventTypes[birth]": True,
        "eventTypes[death]": True,
        "relations[self]": True,
        "sources[gedcom]": True,
        "vague": False,
    }
    res  = client.get(f"/api/trees/{uploaded_tree_id}/visible-counts", query_string=params)
    data = res.get_json()

    assert res.status_code == 200
    assert isinstance(data["people"],   int)
    assert isinstance(data["families"], int)
    assert isinstance(data["events"],   dict)
