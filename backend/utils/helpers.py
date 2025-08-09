# helpers.py
# Created: 2025-04-06 16:00:50
# Edited by: King
# Description: Utility functions like name normalization, fuzzy matching, etc.

import re
import os
import json
import tempfile
import logging
from backend.utils.logger import get_logger

from pathlib import Path

from datetime import datetime
from fuzzywuzzy import fuzz
from sqlalchemy.orm import sessionmaker
from dateutil.parser import parse as _date_parse


from backend.db import get_engine
from backend.config import settings


logger = get_logger(__name__)
from typing import Optional, Tuple

# Optional phonetic lib (Double Metaphone). Keep optional to avoid hard dep.
try:
    from metaphone import doublemetaphone as _double_metaphone
except Exception:  # pragma: no cover - optional dependency
    _double_metaphone = None



def normalize_location(raw_name: str) -> Optional[str]:
    logger.debug("🌍 normalize_location called with: %s", raw_name)

    if not raw_name or not isinstance(raw_name, str):
        logger.warning("⚠️ normalize_location got bad input: %s", raw_name)
        return None

    parts = [p.strip().lower() for p in raw_name.split(",") if p.strip()]
    if len(parts) < 2:
        logger.warning("🟠 Vague or incomplete location: '%s' → parts=%s", raw_name, parts)
        return None

    clean_parts = []
    for p in parts:
        slug = re.sub(r'[^a-z0-9]+', '_', p).strip("_")
        if slug:
            clean_parts.append(slug)

    result = "_".join(clean_parts)
    logger.debug("✅ normalize_location → '%s'", result or "<empty>")
    return result


def normalize_name(name):
    """Lowercase and strip whitespace."""
    result = name.strip().lower()
    logger.debug("👤 normalize_name → '%s' → '%s'", name, result)
    return result


def calculate_name_similarity(name1, name2):
    """Calculate fuzzy matching score between two names."""
    name1_norm = normalize_name(name1)
    name2_norm = normalize_name(name2)
    score = fuzz.ratio(name1_norm, name2_norm)
    logger.debug("🔍 name similarity: '%s' <-> '%s' = %d", name1_norm, name2_norm, score)
    return score


def calculate_match_score(individual1, individual2):
    """Compute a basic match score."""
    score = 0
    if hasattr(individual1, 'name') and hasattr(individual2, 'name'):
        score += calculate_name_similarity(individual1.name, individual2.name)
    logger.debug("🧠 match score: %s vs %s = %d", individual1.name, individual2.name, score)
    return score


def get_db_connection():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()



def print_json(obj):
    def convert(o):
        if isinstance(o, datetime):
            return o.isoformat()
        return str(o)
    logger.info("📝 Printing JSON object")
    logger.info("%s", json.dumps(obj, indent=2, ensure_ascii=False, default=convert))


def normalize_confidence_score(value):
    mapping = {
        "very high": 0.95,
        "high": 0.85,
        "medium": 0.5,
        "low": 0.25,
        "very low": 0.1,
        "unknown": 0.0,
        None: 0.0,
    }
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return mapping.get(value.strip().lower(), 0.0)
    return 0.0


BASE_DIR = Path(__file__).resolve().parents[1]
UNRESOLVED_PATH = os.getenv(
    "UNRESOLVED_PATH",
    str(BASE_DIR / "data" / "unresolved_locations.json"),
)
UPLOAD_COUNT_PATH = os.getenv(
    "UPLOAD_COUNT_PATH",
    str(BASE_DIR / "data" / "upload_count.txt"),
)

def generate_temp_path(suffix=".ged"):
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="gedcom_", text=True)
    os.close(fd)
    logger.debug("📄 Temp file generated at: %s", path)
    return path


def _ensure_upload_count_file() -> None:
    """Create the upload counter file if it doesn't exist."""
    directory = os.path.dirname(UPLOAD_COUNT_PATH)
    os.makedirs(directory, exist_ok=True)
    if not os.path.exists(UPLOAD_COUNT_PATH):
        with open(UPLOAD_COUNT_PATH, "w", encoding="utf-8") as fh:
            fh.write("0")


def read_upload_count() -> int:
    """Return the integer stored in upload_count.txt (0 if missing)."""
    try:
        _ensure_upload_count_file()
        with open(UPLOAD_COUNT_PATH, "r", encoding="utf-8") as fh:
            return int(fh.read().strip() or 0)
    except Exception as exc:
        logger.warning("⚠️ Could not read upload count: %s", exc)
        return 0


def write_upload_count(value: int) -> None:
    """Write the integer value to upload_count.txt."""
    try:
        _ensure_upload_count_file()
        with open(UPLOAD_COUNT_PATH, "w", encoding="utf-8") as fh:
            fh.write(str(value))
    except Exception as exc:
        logger.error("❌ Failed writing upload count: %s", exc)


def increment_upload_count() -> int:
    """Increment and persist the upload counter, returning the new value."""
    count = read_upload_count() + 1
    write_upload_count(count)
    return count


def split_full_name(full_name: str):
    parts = (full_name or "").strip().split(" ", 1)
    first = parts[0] if parts else ""
    last = parts[1] if len(parts) > 1 else ""
    logger.debug("👥 split name → first='%s', last='%s'", first, last)
    return first, last


# backend/utils/helpers.py

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points (in km). Returns 0.0 if any value missing."""
    try:
        from math import radians, sin, cos, asin, sqrt
        if None in (lat1, lon1, lat2, lon2):
            return 0.0
        rlat1, rlon1, rlat2, rlon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
        dlat = rlat2 - rlat1
        dlon = rlon2 - rlon1
        a = sin(dlat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        R = 6371.0
        return float(R * c)
    except Exception:
        return 0.0


def phonetic_keys(name: str) -> Tuple[str, str]:
    """
    Return Double Metaphone primary/secondary keys for a name.
    If the `metaphone` package is unavailable, fall back to a naive key.
    """
    if not name:
        return ("", "")
    if _double_metaphone:
        try:
            p, s = _double_metaphone(str(name))
            return (p or "", s or "")
        except Exception:
            pass
    # Fallback: consonant-only uppercase + truncate
    import re as _re
    base = _re.sub(r"[^A-Za-z]", "", str(name)).upper()
    base = _re.sub(r"[AEIOUY]", "", base)  # strip vowels
    if not base:
        base = str(name).upper()[:4]
    return (base[:6], base[:6])

def parse_date_flexible(value: str):
    """
    Try to parse a GEDCOM date string into a datetime.
    Returns None on failure.
    """
    try:
        return _date_parse(value, fuzzy=True)
    except Exception:
        return None
