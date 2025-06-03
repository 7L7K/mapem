"""
Normalize, classify, and (when possible) geocode raw place strings
coming from GEDCOM uploads. All heavy lifting for historical beats,
manual overrides, vague state tagging, and unresolved logging
happens here.
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Optional

from backend.utils.helpers import normalize_location
from backend.utils.logger import get_logger
from backend.models.location_models import LocationOut

logger = get_logger(__name__)

DEFAULT_FIXES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "manual_place_fixes.json")

# ─── File paths ─────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
MANUAL_FIXES_PATH = os.path.join(DATA_DIR, "manual_place_fixes.json")
UNRESOLVED_LOG_PATH = os.path.join(DATA_DIR, "unresolved_locations.jsonl")

# ─── Keep track of what we've written this run ──────────────────
_SEEN_UNRESOLVED: set[str] = set()

# ─── Load manual fixes (key = normalized place) ────────────────
def _load_manual_fixes() -> Dict[str, Dict]:
    if not os.path.exists(MANUAL_FIXES_PATH):
        logger.warning("⚠️ manual_place_fixes.json not found.")
        return {}
    try:
        with open(MANUAL_FIXES_PATH) as f:
            raw = json.load(f)
        logger.debug(f"✅ Loaded {len(raw)} manual place fixes")
        return {normalize_location(k): v for k, v in raw.items()}
    except Exception as e:
        logger.error(f"❌ Failed loading manual fixes: {e}")
        return {}

MANUAL_FIXES = _load_manual_fixes()

# ─── Exportable helper ─────────────────────────────────────────
def load_manual_place_fixes(path=None):
    path = path or os.path.join(os.path.dirname(__file__), "..", "data", "manual_place_fixes.json")
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load manual fixes: {e}")
    return {}

def log_unresolved_location(
    raw_name: str,
    reason: str,
    status: str,
    source_tag: str = "unknown",
    suggested_fix: Optional[str] = None,
    tree_id: Optional[str] = None,
) -> None:
    entry = {
        "raw_name": raw_name,
        "source_tag": source_tag,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "status": status,
        "suggested_fix": suggested_fix,
        "tree_id": tree_id,
    }
    try:
        with open(UNRESOLVED_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
        logger.warning(f"📝 [unresolved logged] {entry}")
    except Exception as e:
        logger.error(f"❌ failed to write unresolved_location for '{raw_name}': {e}")

def _log_unresolved_once(place: str, reason: str, tree_id: Optional[str] = None) -> None:
    key = f"{place}|{reason}|{tree_id}"
    if key in _SEEN_UNRESOLVED:
        logger.debug(f"🔁 already saw unresolved {key}, skipping write")
        return
    _SEEN_UNRESOLVED.add(key)
    log_unresolved_location(raw_name=place, reason=reason, status="manual_fix_pending", tree_id=tree_id)

def process_location(
    raw_place: str,
    source_tag: str = "",
    event_year: Optional[int] = None,
    tree_id: Optional[str] = None
) -> LocationOut:
    normalized = normalize_location(raw_place)
    now = datetime.now(timezone.utc).isoformat()

    logger.debug(f"🌍 process_location start: raw='{raw_place}' normalized='{normalized}'")

    # 1) empty → nothing after normalizing
    if not normalized:
        logger.warning(f"⚠️ normalized to empty: '{raw_place}' (tree_id: {tree_id})")
        _log_unresolved_once(raw_place, "empty_after_normalise", tree_id=tree_id)
        return LocationOut(
            raw_name=raw_place,
            normalized_name="",
            latitude=None, 
            longitude=None,
            confidence_score=0.0,
            status="unresolved", 
            source="unknown",
            timestamp=now,
        )

    # 2) manual fix override
    if normalized in MANUAL_FIXES:
        manual = MANUAL_FIXES[normalized]
        logger.debug(f"🔧 manual fix hit: '{normalized}' → {manual}")
        return LocationOut(
            raw_name=manual.get("raw_name", raw_place),
            normalized_name=manual.get("normalized_name", normalized),
            latitude=manual.get("latitude"),
            longitude=manual.get("longitude"),
            confidence_score=manual.get("confidence_score", 1.0),
            status="manual_fix", source="manual",
            timestamp=now,
        )

    # 3) vague (no comma → probably just state/county)
    if "," not in raw_place:
        # pre-1890 gets its own tag
        status = (
            "vague_state_pre1890"
            if event_year is not None and event_year < 1890
            else "vague_state"
        )
        return LocationOut(
            raw_name=raw_place,
            normalized_name="",
            latitude=None,
            longitude=None,
            confidence_score=0.5,
            status=status,
            source="vague",
            timestamp=now,
        )

    # 4) give up → unresolved
    logger.error(f"❌ unresolved: '{normalized}' (no match, tree_id: {tree_id})")
    _log_unresolved_once(raw_place, "no_manual_match", tree_id=tree_id)
    return LocationOut(
        raw_name=raw_place,
        normalized_name=normalized,
        latitude=None, longitude=None,
        confidence_score=0.5,
        status="unresolved", source="manual",
        timestamp=now,
    )
