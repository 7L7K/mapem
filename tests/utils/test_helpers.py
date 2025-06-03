import os
import tempfile
from flask import Flask
from backend.db import get_engine
from sqlalchemy.orm import sessionmaker

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

def upload_tiny_tree_and_get_ids(client, tree_name="TinyTestTree"):
    # Write sample GEDCOM to a temp file
    with tempfile.NamedTemporaryFile(mode='w+', suffix=".ged", delete=False) as tmp:
        tmp.write(GEDCOM_SAMPLE.strip())
        tmp.flush()
        temp_path = tmp.name

    try:
        # Upload the file
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/api/upload/",
                data={"file": (f, "tiny_test.ged"), "tree_name": tree_name},
                content_type="multipart/form-data",
            )

        assert response.status_code == 200, f"Upload failed: {response.data}"
        data = response.get_json()

        version_id = data.get("version_id")
        uploaded_id = data.get("tree_id")
        assert version_id, "❌ version_id missing in upload response"
        return version_id, uploaded_id
    finally:
        os.unlink(temp_path)
