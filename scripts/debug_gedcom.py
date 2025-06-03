import argparse
import json
import os
import re
import time
from collections import Counter
from datetime import datetime


PLAC_RE = re.compile(r"^\d+ +PLAC +(.*)")
INDI_RE = re.compile(r"^0 +@I\w+@ +INDI")
FAM_RE = re.compile(r"^0 +@F\w+@ +FAM")
HEADER_NAME_RE = re.compile(r"^1 +NAME +(.*)")
HEADER_TITL_RE = re.compile(r"^1 +TITL +(.*)")


def analyse_gedcom(path: str, max_preview_lines: int = 15):
    start_total = time.perf_counter()
    report = {
        "path": os.path.abspath(path),
        "exists": os.path.exists(path),
        "checked_at": datetime.now().isoformat(),
        "preview_lines": [],
    }
    if not report["exists"]:
        return report

    report["size_bytes"] = os.path.getsize(path)

    start_read = time.perf_counter()
    unresolved_places = []
    vague_places = []
    counts = Counter()

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            line = line.rstrip("\n")
            if i < max_preview_lines:
                report["preview_lines"].append(line)

            if INDI_RE.match(line):
                counts["individuals"] += 1
            elif FAM_RE.match(line):
                counts["families"] += 1

            m = PLAC_RE.match(line)
            if m:
                place = m.group(1).strip()
                counts["places_total"] += 1
                if place == "":
                    unresolved_places.append(place)
                elif place.count(",") < 1:
                    vague_places.append(place)

            # capture header title / name (first occurrence)
            if "tree_name" not in report:
                if (hm := HEADER_TITL_RE.match(line)) or (hm := HEADER_NAME_RE.match(line)):
                    report["tree_name"] = hm.group(1).strip()

    report["parse_time_ms"] = round((time.perf_counter() - start_read) * 1000, 2)
    report.update(counts)
    report["unresolved_place_samples"] = unresolved_places[:10]
    report["vague_place_samples"] = vague_places[:10]
    report["total_time_ms"] = round((time.perf_counter() - start_total) * 1000, 2)
    return report


def main():
    parser = argparse.ArgumentParser(description="Pre‑flight debugger for GEDCOM files before uploading.")
    parser.add_argument("gedcom", help="Path to .ged file")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text")
    args = parser.parse_args()

    report = analyse_gedcom(args.gedcom)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"✅ File: {report['path']}")
        if not report["exists"]:
            print("❌ File does not exist")
            return
        print(f"Size: {report['size_bytes']:,} bytes | Parsed in {report['parse_time_ms']} ms (total {report['total_time_ms']} ms)")
        tree_name = report.get("tree_name", "<not found – you may need to add --form \"tree_name=...\" when uploading>")
        print(f"Tree name: {tree_name}\n")
        print("Counts:")
        for k in ("individuals", "families", "places_total"):
            print(f"  {k:15}: {report.get(k, 0):,}")
        if report["unresolved_place_samples"]:
            print("\n⚠️  Empty place-tags (first 10 shown):")
            for p in report["unresolved_place_samples"]:
                print("  • <empty>")
        if report["vague_place_samples"]:
            print("\n🔍 Possibly vague places (first 10 shown):")
            for p in report["vague_place_samples"]:
                print(f"  • {p}")
        print("\nPreview:")
        for line in report["preview_lines"]:
            print(f"  {line}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())