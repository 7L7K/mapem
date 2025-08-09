#!/usr/bin/env python3
"""Generate simple stats from unresolved_locations.json.

Outputs:
- Top failing place names
- Source breakdown by `source_tag`
"""

import json
from collections import Counter
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "backend" / "data" / "unresolved_locations.json"
TOP_N = 10


def main():
    if not DATA_PATH.exists():
        print(f"❌ File not found: {DATA_PATH}")
        return

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse {DATA_PATH}: {e}")
            return

    if not isinstance(data, list):
        print("❌ Unexpected format: expected a list of entries")
        return

    names = [
        (e.get("raw_name") or e.get("place") or "").strip()
        for e in data
        if (e.get("raw_name") or e.get("place"))
    ]
    top_counts = Counter(names).most_common(TOP_N)

    if top_counts:
        print("\n📊 Top Unresolved Names:")
        for name, count in top_counts:
            print(f"{name}\t{count}")
    else:
        print("No unresolved names found.")

    sources = [str(e.get("source_tag") or "unknown").strip().lower() for e in data]
    source_counts = Counter(sources)
    if source_counts:
        print("\n📈 Source Breakdown:")
        for src, count in source_counts.items():
            print(f"{src}\t{count}")


if __name__ == "__main__":
    main()
