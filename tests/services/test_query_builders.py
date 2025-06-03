import datetime as _dt
import pytest
from backend.db import SessionLocal
from backend.models import UploadedTree, TreeVersion, Event
from backend.services.query_builders import build_event_query
from backend.services.filters import normalize_filters
from tests.utils.id_factory import next_pk
from backend.models import Individual, Event
from datetime import date
from backend.models import event_participants






# ─── fixture ──────────────────────────────────────────────────────────
@pytest.fixture
def seeded_tree_and_events(db_session):
    ut = UploadedTree(  tree_name="QB Test")
    db_session.add(ut); db_session.flush()

    tv = TreeVersion( 
                     uploaded_tree_id=ut.id,
                     version_number=1)
    db_session.add(tv); db_session.flush()

    db_session.add_all([
        Event(  tree_id=tv.id,
              event_type="birth", date=_dt.date(1875, 1, 1)),
        Event(  tree_id=tv.id,
              event_type="death", date=_dt.date(1920, 1, 1)),
    ])
    db_session.commit()
    return tv.id


# ─── tests ────────────────────────────────────────────────────────────
def test_query_with_basic_year_range(db_session, seeded_tree_and_events):
    filters = {
        "year": {"min": 1800, "max": 1950},
        "eventTypes": {"birth": True, "death": True},
        "relations": {}, "sources": {}, "vague": False, "person": ""
    }
    q = build_event_query(db_session, tree_id=seeded_tree_and_events, filters=filters)
    rows = q.all()

    assert len(rows) == 2
    assert {r.event_type for r in rows} == {"birth", "death"}


def test_query_filters_out_death_events(db_session, seeded_tree_and_events):
    filters = {
        "year": {"min": 1800, "max": 1950},
        "eventTypes": {"birth": True, "death": False},
        "relations": {}, "sources": {}, "vague": False, "person": ""
    }
    rows = build_event_query(db_session, seeded_tree_and_events, filters).all()

    assert all(r.event_type == "birth" for r in rows)


def test_event_query_builds_ok():
    filters = normalize_filters({
        "eventTypes": ["birth"],
        "sources": ["manual"],
        "year": {"min": 1800, "max": 2000},
    })
    session = SessionLocal()
    try:
        str(build_event_query(session, tree_id=1, filters=filters))  # compile-time only
    finally:
        session.close()


def test_query_with_event_type_filter(db_session, seeded_tree_and_events):
    filters = {
        "eventTypes": {"birth": True, "death": False},
        "year": {"min": 1800, "max": 2000},
        "relations": {}, "sources": {}, "vague": False, "person": ""
    }
    rows = build_event_query(db_session, seeded_tree_and_events, filters).all()
    assert all(row.event_type == "birth" for row in rows)


from uuid import uuid4

def test_query_filters_by_participant(db_session, seeded_tree_and_events):
    tree_id = seeded_tree_and_events

    alice = Individual(
        tree_id=tree_id,
        gedcom_id="I001",
        first_name="Alice",
        last_name="Wright",
    )
    bob = Individual(
        tree_id=tree_id,
        gedcom_id="I002",
        first_name="Bob",
        last_name="Stone",
    )

    db_session.add_all([alice, bob])
    db_session.flush()

    # Create an event and link both participants
    event = Event(tree_id=tree_id, event_type="residence", date=date(1900, 1, 1))
    db_session.add(event)
    db_session.flush()

    db_session.execute(event_participants.insert().values([
        {"event_id": event.id, "individual_id": alice.id},
        {"event_id": event.id, "individual_id": bob.id},
    ]))
    db_session.commit()

    filters = {"person": alice.id, "relations": {}, "vague": False}
    results = build_event_query(db_session, tree_id, filters).all()

    assert len(results) == 1
    assert results[0].id == event.id
