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
from backend.services.geocode import Geocode
from typing import Any


# Initialize your Geocode engine (api_key can come from env or config)
GEOCODER = Geocode(api_key=os.getenv("GEOCODE_API_KEY"))

logger = get_logger(__name__)

DEFAULT_FIXES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "manual_place_fixes.json")

# ─── File paths ─────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
MANUAL_FIXES_PATH = os.path.join(DATA_DIR, "manual_place_fixes.json")
UNRESOLVED_LOG_PATH = os.path.join(DATA_DIR, "unresolved_locations.jsonl")

# ─── Keep track of what we've written this run ──────────────────
_SEEN_UNRESOLVED: set[str] = set()

# ─── Load manual fixes (key = normalized place) ────────────────
def _load_manual_fixes() -> Dict[str, Any]:
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
            status="manual_fix",
            source="manual",
            timestamp=now,
        )

    # 3) Vague state-only fallback logic
    STATE_VAGUE = {
        "mississippi": (32.7364, -89.6678),
        "arkansas": (34.799, -92.199),
        "tennessee": (35.5175, -86.5804),
        "alabama": (32.8067, -86.7911),
        "louisiana": (30.9843, -91.9623),
        "illinois": (40.6331, -89.3985),
        "ohio": (40.4173, -82.9071),
    }

    if normalized in STATE_VAGUE:
        lat, lng = STATE_VAGUE[normalized]
        logger.info(f"🕳️ vague state fallback for '{raw_place}' (→ {lat}, {lng})")
        return LocationOut(
            raw_name=raw_place,
            normalized_name=normalized,
            latitude=lat,
            longitude=lng,
            confidence_score=0.4,
            status="vague_state_pre1890",
            source="fallback",
            timestamp=now,
        )

    # 4) Try API geocode (last resort)
    logger.info(f"🌎 [process_location] Trying API geocode for '{raw_place}' (normalized: '{normalized}')")
    geo_result = GEOCODER.get_or_create_location(None, raw_place)
    if geo_result and geo_result.latitude and geo_result.longitude:
        logger.info(f"✅ [process_location] Geocoded: '{raw_place}' → {geo_result.latitude}, {geo_result.longitude}")
        geo_result.status = "ok"
        geo_result.source = geo_result.source or "api"
        geo_result.timestamp = now
        return geo_result

    # 5) Still nothing → mark unresolved and log
    logger.error(f"❌ [process_location] Could NOT geocode '{raw_place}' (normalized: '{normalized}')")
    _log_unresolved_once(raw_place, "api_failed", tree_id=tree_id)
    return LocationOut(
        raw_name=raw_place,
        normalized_name=normalized,
        latitude=None,
        longitude=None,
        confidence_score=0.0,
        status="unresolved",
        source="api",
        timestamp=now,
    )
