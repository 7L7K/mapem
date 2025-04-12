#!/usr/bin/env python

import sys, os
from backend.parser import GEDCOMParser
from backend.geocode import Geocode
from backend.utils import get_db_connection
from backend.models import UploadedTree
from sqlalchemy.orm import Session

def load_tree(filepath, uploader="King", tree_name=None):
    tree_name = tree_name or os.path.basename(filepath)
    parser = GEDCOMParser(filepath)
    parser.parse_file()

    session = get_db_connection()

    # Add a row to UploadedTree so we get a tree_id
    tree = UploadedTree(
        original_filename=tree_name,
        uploader_name=uploader,
        notes=""
    )
    session.add(tree)
    session.flush()
    tree_id = tree.id

    print(f"🧬 Uploading tree '{tree_name}' (id={tree_id})...")

    result = parser.save_to_db(
        session=session,
        tree_id=tree_id,
        geocode_client=Geocode(),  # ← enables geocoding & location linking
        dry_run=False              # ← set to True to test only
    )

    session.commit()
    session.close()

    print(f"✅ Upload complete: {result['people_count']} people, {result['event_count']} events added.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/load_gedcom.py path/to/file.ged")
        sys.exit(1)

    filepath = sys.argv[1]
    load_tree(filepath)
