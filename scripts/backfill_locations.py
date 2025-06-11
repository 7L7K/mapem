import os
import sys
import json
import logging
import argparse
from backend.config import DATA_DIR
from sqlalchemy.orm import sessionmaker
from backend.db import get_engine
from backend.models.location import Location, LocationStatusEnum
from backend.utils.helpers import normalize_location as normalize_location_name
from sqlalchemy import or_


log = logging.getLogger("backfill")
logging.basicConfig(level=logging.INFO, format="%(message)s")

def load_locations_from_json(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ File not found: {path}")
    with open(path, "r") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=str(DATA_DIR / "unresolved_locations.json"))
    args = parser.parse_args()

    unresolved = load_locations_from_json(args.file)
    log.info(f"📦 Loaded {len(unresolved)} unresolved entries from {args.file}")

    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    inserted = 0
    for entry in unresolved:
        raw = entry.get("raw_name") or entry.get("place")

        if not raw:
            continue
        normalized = normalize_location_name(raw)
        exists = (
            session.query(Location)
            .filter(or_(Location.raw_name == raw, Location.normalized_name == normalized))
            .first()
        )

        if exists:
            continue
        normalized = normalize_location_name(raw)
        loc = Location(
            raw_name=raw,
            normalized_name=normalized,
            status=LocationStatusEnum.unresolved,
            source="backfill_script"
        )
        session.add(loc)
        inserted += 1

        if not args.dry_run:
            session.commit()
        else:
            session.rollback()
            log.info("💧 Dry run: rolled back all inserts.")
    log.info(f"✅ Inserted {inserted} new unresolved locations")

if __name__ == "__main__":
    main()
