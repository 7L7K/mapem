# tests/routes/test_trees.py
import uuid
from datetime import datetime, timezone
import pytest

from backend.models import UploadedTree, TreeVersion

def _make_uploaded_tree(db_session, name="Test Tree"):
    now = datetime.now(timezone.utc)
    tree = UploadedTree(
        id=uuid.uuid4(),
        tree_name=name,
        uploader_name="TestUser",
        created_at=now,
        updated_at=now,
    )
    db_session.add(tree)
    db_session.commit()
    return tree

from datetime import datetime, timezone
import uuid

def _make_tree_with_version(db_session):
    now = datetime.now(timezone.utc)

    # 1️⃣  create the upload record
    uploaded_tree = UploadedTree(
        id=uuid.uuid4(),
        tree_name="Test Tree",
        uploader_name="TestUser",
        created_at=now,
        updated_at=now,
    )
    db_session.add(uploaded_tree)
    db_session.flush()          # get PK

    # 2️⃣  add an initial TreeVersion that points to it
    version = TreeVersion(
        id=uuid.uuid4(),
        uploaded_tree_id=uploaded_tree.id,
        version_number=1,
        status="active",
        created_at=now,
        updated_at=now,
    )
    db_session.add(version)
    db_session.commit()

    return uploaded_tree        # all tests only need this handle

# ─── BAD FILTERS ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize("bad_payload", [
    {"eventTypes": "not-a-dict"},
    {"eventTypes": None},
    {"eventTypes": {"birth": "yes"}},
    {"eventTypes": {"123": True}},
    {"yearRange": "1800-1900"},
    {"yearRange": [1800]},
    {"sources": "gedcom"},
    {"sources": {"gedcom": "true"}},
    {"relations": 1234},
    {"relations": {"self": "yes"}},
    {"vague": "maybe"},
    {"confidenceThreshold": "high"},
])
def test_visible_counts_rejects_bad_filters(client, db_session, bad_payload):
    tree = _make_tree_with_version(db_session)
    res = client.post(f"/api/trees/{tree.id}/visible-counts", json=bad_payload)
    assert res.status_code == 400, f"Failed on: {bad_payload}"

# ─── TREEVERSION MISMATCH ────────────────────────────────────────────────────
def test_visible_counts_version_mismatch(client, db_session):
    tree_a = _make_uploaded_tree(db_session, "Tree A")
    tree_b = _make_uploaded_tree(db_session, "Tree B")

    version = TreeVersion(
        id=str(uuid.uuid4()),
        uploaded_tree_id=tree_b.id,
        version_number=1,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(version)
    db_session.commit()

    # tree A has no version; should 404
    res = client.post(f"/api/trees/{tree_a.id}/visible-counts", json={"eventTypes": {}})
    assert res.status_code == 404

# ─── TREE COUNTS ON MISSING TREEVERSION ──────────────────────────────────────
def test_tree_counts_treeversion_missing(client, db_session):
    tree = _make_uploaded_tree(db_session, "NoVersion Tree")
    res = client.get(f"/api/trees/{tree.id}/counts")
    assert res.status_code == 404

# ─── NON-EXISTENT TREE ID ────────────────────────────────────────────────────
def test_visible_counts_tree_not_found(client):
    non_existent_id = str(uuid.uuid4())
    res = client.post(f"/api/trees/{non_existent_id}/visible-counts", json={"eventTypes": {}})
    assert res.status_code == 404

# ─── EMPTY PAYLOAD ───────────────────────────────────────────────────────────
def test_visible_counts_empty_payload(client, db_session):
    tree = _make_tree_with_version(db_session)
    res = client.post(f"/api/trees/{tree.id}/visible-counts", json={})
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, dict)
    assert "people" in data or "families" in data
