from __future__ import annotations

"""
Quick seed data generator for local dev.

Creates:
- 1 UploadedTree + TreeVersion
- 2 Individuals
- 1 Location (with lat/lng)
- Birth/Death events for each individual

Usage:
  python scripts/seed_data.py
"""

import uuid
from datetime import date

from backend.db import SessionLocal
from backend.models import UploadedTree, TreeVersion, Individual, Location, Event


def main():
    with SessionLocal.begin() as db:
        upload = UploadedTree(tree_name="Sample Tree", uploader_name="Seed")
        db.add(upload)
        db.flush()

        version = TreeVersion(uploaded_tree_id=upload.id, version_number=1)
        db.add(version)
        db.flush()

        loc = Location(
            raw_name="Boston, Massachusetts, USA",
            normalized_name="Boston, Massachusetts, USA",
            latitude=42.3601,
            longitude=-71.0589,
            confidence_score=1.0,
            source="seed",
            status="ok",
        )
        db.add(loc)
        db.flush()

        a = Individual(
            id=uuid.uuid4(),
            tree_id=version.id,
            gedcom_id="I1",
            first_name="John",
            last_name="Doe",
            occupation="Farmer",
        )
        b = Individual(
            id=uuid.uuid4(),
            tree_id=version.id,
            gedcom_id="I2",
            first_name="Jane",
            last_name="Doe",
            occupation="Teacher",
        )
        db.add_all([a, b])
        db.flush()

        db.add_all([
            Event(event_type="birth", date=date(1850, 5, 12), location_id=loc.id, tree_id=version.id, participants=[a]),
            Event(event_type="death", date=date(1920, 3, 2),  location_id=loc.id, tree_id=version.id, participants=[a]),
            Event(event_type="birth", date=date(1855, 7, 3),  location_id=loc.id, tree_id=version.id, participants=[b]),
        ])

    print("✅ Seed data inserted.")


if __name__ == "__main__":
    main()


