import pytest
from backend.services.parser import GEDCOMParser
from backend.models import Individual, Event, UploadedTree, TreeVersion
from backend.services.gedcom_normalizer import parse_date_flexible
from datetime import datetime


@pytest.fixture
def dummy_location_service():
    class Dummy:
        def resolve_location(self, **kwargs):
            class Out:
                normalized_name = "fake_loc"
                raw_name = "Fake, Place"
                latitude = 1.0
                longitude = 2.0
                confidence_score = 1.0
                status = "ok"
                source = "dummy"
            return Out()
    return Dummy()


GEDCOM_TEST_FILE = "tests/data/test_family_events.ged"

print("GEDCOMParser method list:", dir(GEDCOMParser))

from datetime import datetime, timezone

from uuid import uuid4

def create_dummy_tree(session):
    now = datetime.now(timezone.utc)
    uploaded = UploadedTree(
        id=uuid4(),  # ✅ native UUID, not str
        tree_name="Dummy Tree",
        uploader_name="Test",
        created_at=now,
        updated_at=now,
    )
    session.add(uploaded)
    session.flush()

    version = TreeVersion(
        id=uuid4(),  # ✅ same here
        uploaded_tree_id=uploaded.id,
        version_number=1,
        status="active",
        created_at=now,
        updated_at=now,
    )
    session.add(version)
    session.commit()
    return version.id


def test_marriage_fanout(db_session, dummy_location_service):
    tree_id = create_dummy_tree(db_session)

    parser = GEDCOMParser(GEDCOM_TEST_FILE, dummy_location_service)
    parser.parse_file()
    parser.save_to_db(db_session, tree_id=tree_id, dry_run=False)

    people = db_session.query(Individual).filter_by(tree_id=tree_id).all()
    assert len(people) == 2
    names = set(p.first_name for p in people)
    assert names == {"John", "Jane"}

    events = db_session.query(Event).filter_by(tree_id=tree_id, event_type="marriage").all()
    assert len(events) == 2


def test_parser_stores_event_dates(db_session, dummy_location_service):
    tree_id = create_dummy_tree(db_session)

    parser = GEDCOMParser(GEDCOM_TEST_FILE, dummy_location_service)
    parser.parse_file()
    parser.save_to_db(db_session, tree_id=tree_id)

    events = db_session.query(Event).filter_by(tree_id=tree_id).all()
    assert events, "No events were saved"
    assert all(e.date is not None for e in events)


def test_missing_event_type_is_skipped(db_session, dummy_location_service):
    tree_id = create_dummy_tree(db_session)

    parser = GEDCOMParser(file_path="", location_service=dummy_location_service)
    parser.data = {
        "individuals": [],
        "families": [],
        "events": [
            {"event_type": None, "location": "test", "date": "1 JAN 1900"}
        ]
    }

    summary = parser.save_to_db(db_session, tree_id=tree_id)
    assert summary["event_count"] == 0
    assert any("Missing event_type" in w for w in summary["warnings"])
print("✅ parser.py LOADED")

from importlib import reload
import backend.services.parser as parser_mod
reload(parser_mod)
from backend.services.parser import GEDCOMParser
print("✅ after reload:", "save_to_db" in dir(GEDCOMParser))
