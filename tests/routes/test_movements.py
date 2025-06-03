import pytest
from flask import json
import datetime as dt

from backend.models import UploadedTree, TreeVersion, Individual, Event, Location
from backend.db import get_db
from backend.models import event_participants
from backend.main import create_app


# ─── /api/movements/<tree_id> tests ───────────────────────────────────────────
@pytest.fixture
def test_movements_404_on_missing_tree(client):
    fake_id = "11111111-2222-3333-4444-555555555555"
    response = client.get(f"/api/movements/{fake_id}")
    assert response.status_code == 404
    assert b"not found" in response.data.lower()
    print("🔥 Response status:", response.status)
    print("🔥 Response data:", response.data.decode())



def test_event_with_null_location_id_is_skipped(client):
    with client.application.app_context():
        db = next(get_db())

        uploaded_tree = UploadedTree(tree_name="Null Location Tree", uploader_name="test")
        db.add(uploaded_tree)
        db.flush()

        tree = TreeVersion(uploaded_tree_id=uploaded_tree.id, version_number=1)
        db.add(tree)
        db.flush()

        person = Individual(tree_id=tree.id, gedcom_id="@I1@", first_name="Null", last_name="Case")
        db.add(person)
        db.flush()

        event = Event(tree_id=tree.id, event_type="birth", location_id=None)
        db.add(event)
        db.flush()

        db.execute(event_participants.insert().values(
            event_id=event.id, individual_id=person.id
        ))
        db.commit()

        response = client.get(f"/api/movements/{tree.id}")
        assert response.status_code == 200
        assert response.get_json() == []


def test_valid_location_creates_movement(client):
    with client.application.app_context():
        db = next(get_db())

        uploaded_tree = UploadedTree(tree_name="Movement Tree", uploader_name="test")
        db.add(uploaded_tree)
        db.flush()

        tree = TreeVersion(uploaded_tree_id=uploaded_tree.id, version_number=1)
        db.add(tree)
        db.flush()

        loc = Location(
            raw_name="Greenwood, MS",
            normalized_name="greenwood_ms",
            latitude=33.5162,
            longitude=-90.1790,
            confidence_score=0.9,
            status="ok",
        )
        db.add(loc)
        db.flush()

        person = Individual(tree_id=tree.id, gedcom_id="@I2@", first_name="Move", last_name="Tester")
        db.add(person)
        db.flush()

        event = Event(
            tree_id=tree.id, 
            event_type="birth", 
            location_id=loc.id, 
            date=dt.date(1900, 1, 1)
        )
        db.add(event)
        db.flush()

        db.execute(event_participants.insert().values(
            event_id=event.id, individual_id=person.id
        ))
        db.commit()

        response = client.get(f"/api/movements/{tree.id}")
        assert response.status_code == 200
        data = response.get_json()

        assert isinstance(data, list)
        assert len(data) == 1
        movement = data[0]

        assert movement["event_type"] == "birth"
        assert movement["lat"] == 33.5162
        assert movement["lng"] == -90.1790
        assert movement["location"] == "greenwood_ms"


def test_unresolved_location_logged_correctly(client):
    with client.application.app_context():
        db = next(get_db())

        uploaded_tree = UploadedTree(tree_name="Vague Tree", uploader_name="test")
        db.add(uploaded_tree)
        db.flush()

        tree = TreeVersion(uploaded_tree_id=uploaded_tree.id, version_number=1)
        db.add(tree)
        db.flush()

        unresolved_loc = Location(
            raw_name="Somewhere in Mississippi",
            normalized_name="mississippi",
            latitude=None,
            longitude=None,
            status="vague_state_pre1890",
        )
        db.add(unresolved_loc)
        db.flush()

        person = Individual(tree_id=tree.id, gedcom_id="@I3@", first_name="Vague", last_name="Entry")
        db.add(person)
        db.flush()

        event = Event(tree_id=tree.id, event_type="residence", location_id=unresolved_loc.id)
        db.add(event)
        db.flush()

        db.execute(event_participants.insert().values(
            event_id=event.id, individual_id=person.id
        ))
        db.commit()

        response = client.get(f"/api/movements/{tree.id}")
        assert response.status_code == 200
        assert response.get_json() == []


def test_event_gets_movement_after_location_added(client):
    with client.application.app_context():
        db = next(get_db())

        uploaded = UploadedTree(tree_name="Hotpatch Test Tree")
        db.add(uploaded)
        db.flush()

        tree = TreeVersion(uploaded_tree_id=uploaded.id, version_number=1)
        db.add(tree)
        db.flush()

        person = Individual(tree_id=tree.id, gedcom_id="@I4@", first_name="Hot", last_name="Patch")
        db.add(person)
        db.flush()

        event = Event(
            tree_id=tree.id,
            event_type="birth",
            date=dt.date(1900, 1, 1),
            location_id=None,
        )
        db.add(event)
        db.flush()

        db.execute(event_participants.insert().values(
            event_id=event.id, individual_id=person.id
        ))
        db.commit()

        res = client.get(f"/api/movements/{tree.id}")
        assert res.status_code == 200
        assert res.get_json() == []

        # Add location and patch event
        loc = Location(
            raw_name="Jackson, MS",
            normalized_name="jackson_ms",
            latitude=32.2988,
            longitude=-90.1848,
            confidence_score=0.9,
            status="ok",
        )
        db.add(loc)
        db.flush()

        event.location_id = loc.id
        db.add(event)
        db.commit()

        res2 = client.get(f"/api/movements/{tree.id}")
        assert res2.status_code == 200
        data = res2.get_json()
        assert isinstance(data, list)
        assert len(data) == 1

        m = data[0]
        assert m["event_type"] == "birth"
        assert m["lat"] == 32.2988
        assert m["lng"] == -90.1848
        assert "jackson" in m["location"]
