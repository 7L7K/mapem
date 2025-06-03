from tests.utils.id_factory import next_pk
import datetime as _dt
import uuid

def test_get_people_success(client, db_session):
    from backend.models import UploadedTree, TreeVersion, Individual
    ut = UploadedTree(tree_name="foo")
    db_session.add(ut)
    db_session.flush()

    tv = TreeVersion(tree_id=ut.id, version_number=1)
    db_session.add(tv)
    db_session.flush()

    ind = Individual(
        tree_id=tv.id,
        gedcom_id="I123",  # Required field
        first_name="Jane",
        last_name="Doe"
    )
    db_session.add(ind)
    db_session.commit()

    # Act
    resp = client.get(f"/api/people/{tv.id}?limit=10&offset=0")
    data = resp.get_json()

    # Assert
    assert resp.status_code == 200
    assert "people" in data
    assert isinstance(data, dict)
    assert "people" in data and isinstance(data["people"], list)

    assert len(data["people"]) == 1
    person = data["people"][0]
    assert person["name"] == "Jane Doe"

def test_get_people_success(client, db_session):
    from backend.models import UploadedTree, TreeVersion, Individual

    ut = UploadedTree(tree_name="People-Route Test")
    db_session.add(ut); db_session.flush()

    tv = TreeVersion(
                     uploaded_tree_id=ut.id,
                     version_number=1)
    db_session.add(tv); db_session.flush()

    person = Individual(

        tree_id=tv.id,
        gedcom_id="I123",
        first_name="Jane",
        last_name="Doe",
        birth_date=_dt.date(1888, 1, 1),
    )
    db_session.add(person); db_session.commit()

    resp = client.get(f"/api/people/{ut.id}?limit=10&offset=0")
    data = resp.get_json()

    assert resp.status_code == 200
    assert len(data["people"]) == 1
    assert data["people"][0]["name"] == "Jane Doe"


def test_people_400_on_invalid_uuid(client):
    # Should return 400 for malformed UUIDs
    resp = client.get("/api/people/999999")
    assert resp.status_code == 400
    assert "must be a valid uuid" in resp.json["error"].lower()


def test_people_404_on_valid_but_missing_tree(client):
    # Should return 404 for valid UUID that doesn't match any UploadedTree
    missing_id = uuid.uuid4()
    resp = client.get(f"/api/people/{missing_id}")
    assert resp.status_code == 404
    assert "tree not found" in resp.json["error"].lower()

def test_people_filtering(client, db_session):
    from backend.models import UploadedTree, TreeVersion, Individual

    ut = UploadedTree( tree_name="PeopleFilterTest")
    db_session.add(ut); db_session.flush()

    tv = TreeVersion(  uploaded_tree_id=ut.id, version_number=1)
    db_session.add(tv); db_session.flush()

    people = [
        Individual(  tree_id=tv.id, gedcom_id="I1", first_name="Alice", last_name="Smith"),
        Individual(  tree_id=tv.id, gedcom_id="I2", first_name="Bob", last_name="Jones"),
    ]
    db_session.add_all(people); db_session.commit()

    # should return only Alice
    resp = client.get(f"/api/people/{ut.id}?person=alice")
    data = resp.get_json()
    assert resp.status_code == 200
    assert len(data["people"]) == 1
    assert data["people"][0]["name"].lower() == "alice smith"
