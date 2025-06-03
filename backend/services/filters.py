"""
Normalize raw UI-filter payloads from the front-end and
surface human-readable hints for contradictions.

Returned structure (all keys always present):
{
    "eventTypes":  ["birth", "death", …],
    "year":        {"min": 1700, "max": 2025},
    "vague":       True,
    "confidenceThreshold": 0.0,
    "sources":     ["census", "manual", …],
    "person":      "123",
    "relations":   {"self": True, "siblings": …},
}
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("mapem.filters")

# ─── Reference sets ────────────────────────────────────────────
_VALID_EVENT_TYPES = {
    "birth", "death", "marriage", "burial", "residence", "census",
}
_VALID_SOURCE_TAGS = {
    "gedcom", "census", "manual", *_VALID_EVENT_TYPES,
}

# ─── Tiny helpers ──────────────────────────────────────────────
def _parse_bool(val: Any) -> Optional[bool]:
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        v = val.strip().lower()
        if v in {"true", "1", "yes"}:
            return True
        if v in {"false", "0", "no"}:
            return False
    return None

def _normalise_checkbox_input(raw_val: Any, valid: set[str]) -> List[str]:
    """
    Accepts:
        • list style    → ["birth","death"]
        • dict style    → {"birth":true,"death":false}
    """
    logger.debug("🧪 _normalise_checkbox_input raw=%s", raw_val)
    if raw_val is None:
        return []

    cleaned: List[str] = []

    if isinstance(raw_val, list):
        for item in raw_val:
            if not isinstance(item, str):
                continue
            key = item.lower().strip()
            if key in valid and key not in cleaned:
                cleaned.append(key)
        return cleaned

    if isinstance(raw_val, dict):
        for key, checked in raw_val.items():
            if not isinstance(key, str) or not checked:
                continue
            k = key.lower().strip()
            if k in valid and k not in cleaned:
                cleaned.append(k)
        return cleaned

    return []

def _parse_year(raw_year: Any) -> Dict[str, int]:
    """
    Supports:
        • {min: 1800, max: 1950}
        • [1800,1950]
        • None / {}  → defaults 1700-<this year>
    Always guarantees min ≤ max.
    """
    logger.debug("🧪 _parse_year raw=%s", raw_year)
    default_min = 1700
    default_max = datetime.now().year

    if isinstance(raw_year, dict):
        y_min, y_max = raw_year.get("min"), raw_year.get("max")
    elif isinstance(raw_year, list) and len(raw_year) == 2:
        y_min, y_max = raw_year
    else:
        y_min = y_max = None

    try:
        y_min = int(y_min) if y_min is not None else default_min
    except (TypeError, ValueError):
        y_min = default_min
    try:
        y_max = int(y_max) if y_max is not None else default_max
    except (TypeError, ValueError):
        y_max = default_max

    if y_min > y_max:
        y_min, y_max = y_max, y_min

    out = {"min": y_min, "max": y_max}
    logger.debug("🧪 parsed year block → %s", out)
    return out

# ─── Public — normalize & explain ─────────────────────────────
def normalize_filters(raw: Dict[str, Any]) -> Dict[str, Any]:
    logger.debug("🧪 normalize_filters INPUT=%s", raw)
    if not isinstance(raw, dict):
        raise TypeError("filters payload must be a JSON object")

    valid_keys = {
        "eventTypes", "yearRange", "year", "vague",
        "confidenceThreshold", "sources", "person", "relations",
    }
    unknown = set(raw) - valid_keys
    if unknown:
        raise ValueError(f"Invalid filter keys: {', '.join(unknown)}")

    # eventTypes / sources
    event_types = _normalise_checkbox_input(raw.get("eventTypes"), _VALID_EVENT_TYPES)
    sources     = _normalise_checkbox_input(raw.get("sources"),     _VALID_SOURCE_TAGS)

    # year
    yr_raw = raw.get("year") if raw.get("year") not in (None, {}) else raw.get("yearRange")
    year_block = _parse_year(yr_raw)

    # vague toggle
    vague = _parse_bool(raw.get("vague"))
    vague = True if vague is None else vague

    # confidence
    try:
        conf = float(raw.get("confidenceThreshold", 0.0) or 0.0)
    except (TypeError, ValueError):
        raise ValueError("confidenceThreshold must be a float")

    # person / relations
    relations = raw.get("relations") if isinstance(raw.get("relations"), dict) else {"self": True}
    person    = str(raw.get("person", "")).strip().lower()

    cleaned = {
        "eventTypes": event_types,
        "year": year_block,
        "vague": vague,
        "confidenceThreshold": conf,
        "sources": sources,
        "person": person,
        "relations": relations,
    }
    logger.debug("✅ normalize_filters OUTPUT=%s", cleaned)
    return cleaned

def explain_filters(filters: Dict[str, Any]) -> Optional[str]:
    yr = filters.get("year", {})
    if yr.get("max") < yr.get("min"):
        return "Year range is inverted."
    return None

# ──────────────────────────────────────────────────────────────
# Parse query-string → dict  so front-end                        │
# can keep using bracket-syntax (?eventTypes[birth]=true …)      │
# ──────────────────────────────────────────────────────────────
from werkzeug.datastructures import MultiDict  # import inside file to avoid circulars

def _safe_strip(v: Any) -> Any:
    return v.strip() if isinstance(v, str) else v

def from_query_args(args: Any) -> Dict[str, Any]:
    """
    Accepts:
        • Flask request.args (MultiDict)
        • a plain dict / mapping
        • a dict returned by request.args.to_dict(flat=False)
    Returns structure ready for normalize_filters().
    """
    logger.debug("🧪 from_query_args INPUT=%s", args)

    # Normalise iteration so we always have key → list[values]
    kv_iter: Dict[str, List[Any]] = {}
    if isinstance(args, MultiDict):                      # usual path
        kv_iter = {k: args.getlist(k) for k in args.keys()}
    elif isinstance(args, dict):
        for k, v in args.items():
            kv_iter[k] = v if isinstance(v, list) else [v]
    else:
        raise TypeError("Unsupported arg container")

    filters: Dict[str, Any] = {}

    for key, values in kv_iter.items():
        for value in values:
            # yearRange handled specially
            if key == "yearRange":
                try:
                    filters.setdefault("yearRange", []).append(int(value))
                except ValueError:
                    logger.warning("⚠️ Dropped bad yearRange val: %s", value)
                continue

            # bracket notation  e.g. eventTypes[birth]=true
            if "[" in key and key.endswith("]"):
                base, inner = key.split("[", 1)
                inner = inner[:-1].lower().strip()

                if base not in filters:
                    filters[base] = {}

                is_true = str(value).lower() in {"true", "1", "yes"}
                filters[base][inner] = is_true
                continue

            # simple scalar — but coerce any boolean-like strings
            stripped = _safe_strip(value)
            # if it parses to a bool, use that, otherwise leave the string
            bool_val = _parse_bool(stripped)
            filters[key] = bool_val if bool_val is not None else stripped

    logger.debug("🧪 from_query_args OUTPUT=%s", filters)
    return filters
