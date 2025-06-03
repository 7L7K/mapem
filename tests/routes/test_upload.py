import os
import json
import tempfile

from flask import Flask
from backend.main import create_app
from backend.db import get_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Individual

GEDCOM_SAMPLE = """0 HEAD
1 SOUR test
1 GEDC
2 VERS 5.5
1 CHAR UTF-8
0 @I1@ INDI
1 NAME John /Doe/
1 SEX M
1 BIRT
2 DATE 01 JAN 1900
0 TRLR
"""

def test_upload_tiny_gedcom_populates_names():
    # ─── App + Client ────────────────────────────────────────────────
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    # ─── DB Session ─────────────────────────────────────────────────
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    # ─── Create Temp GEDCOM ─────────────────────────────────────────
    with tempfile.NamedTemporaryFile(mode='w+', suffix=".ged", delete=False) as tmp:
        tmp.write(GEDCOM_SAMPLE.strip())
        tmp.flush()
        temp_path = tmp.name

    try:
        # ─── Upload ────────────────────────────────────────────────
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/api/upload/",
                data={
                    "file": (f, "tiny_test.ged"),
                    "tree_name": "TinyTestTree",
                },
                content_type="multipart/form-data",
            )

        assert response.status_code == 200, f"Upload failed: {response.data}"
        data = response.get_json()

        tree_id = data.get("version_id")
        assert tree_id, "❌ version_id (TreeVersion) missing in response"

        # ─── Check Individuals ─────────────────────────────────────
        people = session.query(Individual).filter_by(tree_id=tree_id).all()
        assert people, "❌ No individuals found after upload"

        for p in people:
            print(f"🧑 ID: {p.id}, First: {p.first_name}, Last: {p.last_name}")
            assert p.first_name and p.first_name.strip(), "❌ Missing first_name"
            assert p.last_name and p.last_name.strip(), "❌ Missing last_name"
            break  # One is enough for this test

    finally:
        os.unlink(temp_path)
        session.close()
