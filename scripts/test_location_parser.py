import re
import json
from pathlib import Path
from backend.utils.helpers import normalize_location

# ─── Helpers ──────────────────────────────────────────────────────────────────

def normalize_string(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r',+', ',', s)
    s = re.sub(r'(, )+', ',', s)
    return s.strip(", ")

# ─── Paths & Load Fixes ───────────────────────────────────────────────────────

PROJECT_ROOT    = Path(__file__).resolve().parents[1]
FIXES_PATH      = PROJECT_ROOT / "backend" / "data" / "manual_place_fixes.json"
UNRESOLVED_PATH = PROJECT_ROOT / "backend" / "data" / "unresolved_locations.json"

try:
    with FIXES_PATH.open() as f:
        raw_fixes = json.load(f)
    MANUAL_FIXES = { normalize_string(k): v for k, v in raw_fixes.items() }
except Exception as e:
    print(f"❌ Could not load manual_place_fixes.json: {e}")
    MANUAL_FIXES = {}

# ─── Classifier ──────────────────────────────────────────────────────────────

def classify_location(raw_name: str) -> dict:
    norm = normalize_string(raw_name)
    fixed = MANUAL_FIXES.get(norm)

    if fixed:
        return {
            "original":   raw_name,
            "normalized": norm,
            "fixed":      fixed,
            "status":     "manual_override",
        }
    elif norm in {"mississippi", "tennessee", "louisiana"}:
        return {
            "original":   raw_name,
            "normalized": norm,
            "fixed":      norm,
            "status":     "vague_state",
        }
    else:
        return {
            "original":   raw_name,
            "normalized": norm,
            "fixed":      None,
            "status":     "unresolved",
        }

# ─── Main ────────────────────────────────────────────────────────────────────

# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    if not UNRESOLVED_PATH.exists():
        print(f"❌ unresolved_locations.json not found at {UNRESOLVED_PATH}")
        return

    with UNRESOLVED_PATH.open() as f:
        data = json.load(f)

    print(f"🔍 Loaded {len(data)} unresolved entries from {UNRESOLVED_PATH}")

    seen = set()
    for entry in data:
        raw = entry.get("raw_name") or entry.get("place")
        if not raw:
            continue
        key = raw.lower()
        if key in seen:
            continue
        seen.add(key)

        result = classify_location(raw)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
