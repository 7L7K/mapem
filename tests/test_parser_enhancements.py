import uuid
from backend.services.parser import GEDCOMParser
from backend.models import Event, Location

class DummyLocSvc:
    def __init__(self, status="ok"):
        self.status = status
    def resolve_location(self, **_kw):
        class Out:
            raw_name = "X"
            normalized_name = "" if self.status != "ok" else "place_x"
            latitude = None
            longitude = None
            confidence_score = 0.0
            status = self.status
            source = "dummy"
        return Out()

def create_tree(session):
    from backend.models import UploadedTree, TreeVersion
    ut = UploadedTree(id=uuid.uuid4(), tree_name="T")
    session.add(ut); session.flush()
    tv = TreeVersion(id=uuid.uuid4(), uploaded_tree_id=ut.id, version_number=1)
    session.add(tv); session.commit()
    return tv.id

def test_duplicate_events_skipped(db_session):
    tree_id = create_tree(db_session)
    parser = GEDCOMParser("tests/data/test_family_events.ged", DummyLocSvc())
    parser.parse_file()
    parser.save_to_db(db_session, tree_id=tree_id)
    count1 = db_session.query(Event).filter_by(tree_id=tree_id).count()
    parser.save_to_db(db_session, tree_id=tree_id)
    count2 = db_session.query(Event).filter_by(tree_id=tree_id).count()
    assert count1 == count2

def test_unresolved_location_skipped(db_session):
    tree_id = create_tree(db_session)
    parser = GEDCOMParser(file_path="", location_service=DummyLocSvc(status="unresolved"))
    parser.data = {
        "individuals": [],
        "families": [],
        "events": [{"event_type": "birth", "location": "Atlantis", "date": "1 JAN 1900"}]
    }
    parser.save_to_db(db_session, tree_id=tree_id)
    # location should not be created
    assert db_session.query(Location).count() == 0
    evt = db_session.query(Event).first()
    assert evt and evt.location_id is None

