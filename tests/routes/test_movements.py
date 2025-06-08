import datetime as dt
import pytest

from backend.models import (
    UploadedTree, TreeVersion, Individual, Family, Location, Event,
    event_participants,
)


def _setup_tree(db_session):
    ut = UploadedTree(tree_name="MoveTree")
    db_session.add(ut); db_session.flush()

    tv = TreeVersion(uploaded_tree_id=ut.id, version_number=1)
    db_session.add(tv); db_session.flush()

    dad = Individual(tree_id=tv.id, gedcom_id="I1", first_name="Dad", last_name="Doe")
    mom = Individual(tree_id=tv.id, gedcom_id="I2", first_name="Mom", last_name="Doe")
    db_session.add_all([dad, mom]); db_session.flush()

    fam = Family(tree_id=tv.id, husband_id=dad.id, wife_id=mom.id)
    db_session.add(fam); db_session.flush()

    loc1 = Location(raw_name="A", normalized_name="a", latitude=1, longitude=1, confidence_score=1, status="ok")
    loc2 = Location(raw_name="B", normalized_name="b", latitude=2, longitude=2, confidence_score=1, status="ok")
    db_session.add_all([loc1, loc2]); db_session.flush()

    e1 = Event(tree_id=tv.id, event_type="birth", date=dt.date(1800,1,1), location_id=loc1.id)
    e2 = Event(tree_id=tv.id, event_type="residence", date=dt.date(1850,1,1), location_id=loc2.id)
    e3 = Event(tree_id=tv.id, event_type="birth", date=dt.date(1805,1,1), location_id=loc1.id)
    e4 = Event(tree_id=tv.id, event_type="residence", date=dt.date(1855,1,1), location_id=loc2.id)
    db_session.add_all([e1,e2,e3,e4]); db_session.flush()

    db_session.execute(event_participants.insert().values([
        {"event_id": e1.id, "individual_id": dad.id},
        {"event_id": e2.id, "individual_id": dad.id},
        {"event_id": e3.id, "individual_id": mom.id},
        {"event_id": e4.id, "individual_id": mom.id},
    ]))
    db_session.commit()
    return ut.id, tv.id, fam.id, dad.id, mom.id


def test_group_by_person(client, db_session):
    tree_id, version_id, fam_id, dad_id, mom_id = _setup_tree(db_session)

    # Add a person with no movements
    person_no_moves = Individual(
        tree_version_id=version_id,
        name="NoMove Person",
        gender="U"
    )
    db_session.add(person_no_moves)
    db_session.commit()

    response = client.get(f"/api/trees/{tree_id}/movements/group_by_person")
    assert response.status_code == 200
    data = response.get_json()

    # Find each person in the response
    dad = next((p for p in data if p["id"] == dad_id), None)
    mom = next((p for p in data if p["id"] == mom_id), None)
    no_move = next((p for p in data if p["id"] == person_no_moves.id), None)

    # Assert dad's movements
    assert dad is not None
    assert isinstance(dad["movements"], list)
    # Example: check that dad has expected movement(s)
    assert any("location" in m and "date" in m for m in dad["movements"])
    # Optionally, check for specific movement content if known

    # Assert mom's movements
    assert mom is not None
    assert isinstance(mom["movements"], list)
    assert any("location" in m and "date" in m for m in mom["movements"])

    # Assert person with no movements
    assert no_move is not None
    assert isinstance(no_move["movements"], list)
    assert len(no_move["movements"]) == 0

    res = client.get(f"/api/movements/{tree_id}?grouped=person")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, dict)
    assert set(data.keys()) == {dad_id, mom_id}


def test_person_ids_filter(client, db_session):
    tree_id, version_id, fam_id, dad_id, mom_id = _setup_tree(db_session)

    res = client.get(f"/api/movements/{tree_id}?grouped=person&personIds={dad_id}")
    assert res.status_code == 200
    data = res.get_json()
    assert list(data.keys()) == [dad_id]


def test_group_by_family(client, db_session):
    tree_id, version_id, fam_id, dad_id, mom_id = _setup_tree(db_session)
    res = client.get(f"/api/movements/{tree_id}?grouped=family&familyId={fam_id}")
    assert res.status_code == 200
    data = res.get_json()
    assert list(data.keys()) == [fam_id]

