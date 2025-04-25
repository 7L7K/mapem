# backend/services/location_processor.py
"""
Normalize, classify, and (when possible) geocode raw place strings
coming from GEDCOM uploads.  All heavy lifting for historical beats,
manual overrides, vague state tagging, and unresolved logging
happens here.
"""
import os, json, re
from datetime import datetime
from typing import Dict, Tuple, Optional

from backend.utils.helpers import normalize_location
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# ─── File paths ─────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
MANUAL_FIXES_PATH = os.path.join(DATA_DIR, "manual_place_fixes.json")
UNRESOLVED_PATH   = os.path.join(DATA_DIR, "unresolved_locations.json")

# ─── Load manual fixes (key = normalized place) ────────────────
def _load_manual_fixes() -> Dict[str, Dict]:
    if not os.path.exists(MANUAL_FIXES_PATH):
        logger.warning("manual_place_fixes.json not found.")
        return {}
    try:
        with open(MANUAL_FIXES_PATH) as f:
            raw = json.load(f)
        return {normalize_location(k): v for k, v in raw.items()}
    except Exception as e:
        logger.error("Failed loading manual fixes: %s", e)
        return {}

MANUAL_FIXES = _load_manual_fixes()

# ─── Main Processor ────────────────────────────────────────────
def process_location(raw_place: str, event_year: Optional[int] = None) -> Tuple[dict, str]:
    """
    Return (location_dict, status)
    status = 'ok' | 'manual_fix' | 'unresolved' | 'vague_state'
    """
    normalized = normalize_location(raw_place)
    if not normalized:
        return {}, "unresolved"

    # 1) Manual override
    if normalized in MANUAL_FIXES:
        logger.debug("Manual fix hit: %s → %s", raw_place, MANUAL_FIXES[normalized])
        return MANUAL_FIXES[normalized], "manual_fix"

    # 2) Historical / vague detection (very simplified for demo)
    if "," not in normalized:  # e.g., "Mississippi"
        logger.info("Vague state-level place captured: %s", raw_place)
        _log_unresolved(raw_place, reason="state_only")
        return {"raw_name": raw_place}, "vague_state"

    # 3) Default – assume ok, geocode happens elsewhere
    return {"raw_name": raw_place, "normalized_name": normalized}, "ok"

# ─── Helpers ───────────────────────────────────────────────────
def _log_unresolved(place: str, reason: str):
    record = {
        "place": place,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    }
    try:
        unresolved = []
        if os.path.exists(UNRESOLVED_PATH):
            with open(UNRESOLVED_PATH) as f:
                unresolved = json.load(f)
        unresolved.append(record)
        with open(UNRESOLVED_PATH, "w") as f:
            json.dump(unresolved, f, indent=2)
    except Exception as e:
        logger.error("Failed to write unresolved log: %s", e)
