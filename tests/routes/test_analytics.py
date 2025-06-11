from backend.models import Location, UploadedTree
from backend.models.enums import LocationStatusEnum


def test_system_snapshot(client, db_session):
    # Setup sample data
    loc1 = Location(raw_name="A", normalized_name="a", status=LocationStatusEnum.ok)
    loc2 = Location(raw_name="B", normalized_name="b", status=LocationStatusEnum.unresolved)
    loc3 = Location(raw_name="C", normalized_name="c", status=LocationStatusEnum.manual_override)
    db_session.add_all([loc1, loc2, loc3])
    tree = UploadedTree(tree_name="T")
    db_session.add(tree)
    db_session.commit()

    resp = client.get("/api/analytics/snapshot")
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["total_locations"] == 3
    assert data["resolved"] == 1
    assert data["unresolved"] == 1
    assert data["manual_fixes"] == 1
    assert "last_upload" in data
