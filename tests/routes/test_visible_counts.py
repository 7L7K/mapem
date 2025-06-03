import pytest
import datetime as dt
from flask import json

from backend.models import UploadedTree, TreeVersion, Individual, Event, Location
from backend.db import get_db
from backend.models import event_participants

def test_visible_counts_returns_data(client):
    with client.application.app_context():
        db = next(get_db())

        # ─── Setup Tree + Version ─────────────────────────────────────────────
        uploaded_tree = UploadedTree(tree_name="Counts Test Tree")
        db.add(uploaded_tree)
        db.flush()

        tree = TreeVersion(uploaded_tree_id=uploaded_tree.id, version_number=1)
        db.add(tree)
        db.flush()

        # ─── Create Location ──────────────────────────────────────────────────
        loc = Location(
            raw_name="Canton, MS",
            normalized_name="canton_ms",
            latitude=32.612,
            longitude=-90.036,
            confidence_score=0.95,
            status="ok",
        )
        db.add(loc)
        db.flush()

        # ─── Add Individual ───────────────────────────────────────────────────
        person = Individual(
            tree_id=tree.id,
            gedcom_id="@I1@",
            first_name="Joe",
            last_name="Tester"
        )
        db.add(person)
        db.flush()

        # ─── Add Event ────────────────────────────────────────────────────────
        event = Event(
            tree_id=tree.id,
            event_type="birth",
            location_id=loc.id,
            date=dt.date(1899, 6, 10),
            source_tag="BIRT",
            category="life_event",
        )
        db.add(event)
        db.flush()

        # ─── Link via event_participants ──────────────────────────────────────
        db.execute(event_participants.insert().values(
            event_id=event.id, individual_id=person.id
        ))

        # ─── Make API Call ────────────────────────────────────────────────────
        response = client.get(f"/api/trees/{tree.id}/counts")
        assert response.status_code == 200

        data = response.get_json()
        print("DEBUG JSON:", data)

        assert "individuals" in data
        assert "families" in data
        assert "events" in data, f"Missing 'events' in response: {data}"

        assert data["individuals"] == 1
        assert isinstance(data["families"], int)
        assert "birth" in data["events"]
        assert data["events"]["birth"] == 1
