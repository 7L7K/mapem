from __future__ import annotations

"""Hydrate gazetteer_entries from TSV or JSON sources (GeoNames/Wikidata).

Usage:
  python -m backend.scripts.load_gazetteer geonames.tsv
  python -m backend.scripts.load_gazetteer data.json
"""

import csv
import json
import sys
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import sessionmaker

from backend.db import engine
from backend.models.gazetteer_entry import GazetteerEntry, compute_era_bucket
from backend.utils.helpers import normalize_location


def iter_rows(path: Path):
    if path.suffix.lower() in {".tsv", ".txt"}:
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                yield row
    else:
        data = json.loads(path.read_text())
        if isinstance(data, list):
            for row in data:
                yield row
        elif isinstance(data, dict):
            for _, row in data.items():
                yield row


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m backend.scripts.load_gazetteer <file>")
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        return 2

    Session = sessionmaker(bind=engine)
    session = Session()
    created = 0
    try:
        for row in iter_rows(path):
            name = normalize_location(row.get("name") or row.get("name_norm") or "")
            if not name:
                continue
            admin = normalize_location(row.get("admin") or row.get("admin_norm") or "") or None
            year = row.get("year")
            try:
                yeari = int(year) if year is not None else None
            except Exception:
                yeari = None
            era = compute_era_bucket(yeari)
            lat = row.get("lat") or row.get("latitude")
            lng = row.get("lng") or row.get("longitude")
            try:
                latf = float(lat)
                lngf = float(lng)
            except Exception:
                continue
            entry = GazetteerEntry(
                name_norm=name,
                admin_norm=admin,
                era_bucket=era,
                latitude=latf,
                longitude=lngf,
                source=row.get("source") or "import",
                source_id=row.get("source_id"),
                country_code=row.get("country_code"),
                admin1=row.get("admin1"),
                admin2=row.get("admin2"),
                alt_names=row.get("alt_names"),
                meta=row.get("meta"),
            )
            session.add(entry)
            created += 1
            if created % 1000 == 0:
                session.commit()
                print(f"Committed {created}...")
        session.commit()
        print(f"✅ Loaded {created} gazetteer entries")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())


