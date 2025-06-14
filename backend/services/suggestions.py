import json
import os
import logging
import requests
from typing import Optional, Dict

# ──────────────────────────────────────────────
# Logger setup (prints in Flask/Celery too)
logger = logging.getLogger("suggestions")
logger.setLevel(logging.DEBUG)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[suggestions] %(levelname)s: %(message)s"))
    logger.addHandler(handler)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MANUAL_FIXES_PATH = os.path.join(BASE_DIR, "data", "manual_place_fixes.json")
HISTORICAL_DIR = os.path.join(BASE_DIR, "data", "historical_places")

# ──────────────────────────────────────────────
# Manual fixes: loaded once, never silent
try:
    with open(MANUAL_FIXES_PATH) as f:
        MANUAL_FIXES = json.load(f)
    logger.debug(f"Loaded {len(MANUAL_FIXES)} manual fixes")
except Exception as e:
    logger.error(f"Failed to load manual fixes from {MANUAL_FIXES_PATH}: {e}")
    MANUAL_FIXES = {}

def get_manual_fix(name: str) -> Optional[Dict]:
    fix = MANUAL_FIXES.get(name)
    logger.debug(f"Manual fix lookup for '{name}': {'HIT' if fix else 'MISS'}")
    return fix

# ──────────────────────────────────────────────
# Historical lookup, can be made year-aware in the future
def lookup_historical(name: str, year: Optional[int]=None) -> Optional[Dict]:
    for fn in os.listdir(HISTORICAL_DIR):
        path = os.path.join(HISTORICAL_DIR, fn)
        try:
            with open(path) as f:
                data = json.load(f)
            # Could be year-specific in the future
            candidate = data.get(name)
            if candidate:
                logger.debug(f"Historical lookup HIT in {fn} for '{name}'")
                return candidate
        except Exception as e:
            logger.warning(f"Error loading {fn} for historical lookup: {e}")
            continue
    logger.debug(f"Historical lookup MISS for '{name}'")
    return None

# ──────────────────────────────────────────────
def call_google(query: str) -> Optional[Dict]:
    key = os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("GEOCODE_API_KEY")
    if not key:
        logger.warning("Google API key missing")
        return None
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": query, "key": key}
    try:
        resp = requests.get(url, params=params, timeout=6)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            logger.info(f"Google found 0 results for '{query}'")
            return None
        top = results[0]
        loc = top["geometry"]["location"]
        suggestion = {
            "lat": loc["lat"],
            "lng": loc["lng"],
            "display_name": top["formatted_address"],
            "source": "google",
            "confidence": "high"
        }
        logger.debug(f"Google suggestion for '{query}': {suggestion}")
        return suggestion
    except Exception as e:
        logger.error(f"Google geocode error for '{query}': {e}")
        return None

def call_nominatim(query: str) -> Optional[Dict]:
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": 1}
    headers = {"User-Agent": "MapEm/1.0"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=7)
        resp.raise_for_status()
        results = resp.json()
        if not results:
            logger.info(f"Nominatim found 0 results for '{query}'")
            return None
        top = results[0]
        suggestion = {
            "lat": float(top["lat"]),
            "lng": float(top["lon"]),
            "display_name": top["display_name"],
            "source": "nominatim",
            "confidence": "medium"
        }
        logger.debug(f"Nominatim suggestion for '{query}': {suggestion}")
        return suggestion
    except Exception as e:
        logger.error(f"Nominatim error for '{query}': {e}")
        return None

# ──────────────────────────────────────────────
def suggest_coordinates(loc) -> Optional[Dict]:
    """
    Try manual fixes → historical → Google → Nominatim.
    `loc` is a Location instance with attributes raw_name, normalized_name, last_seen.
    """
    name = getattr(loc, "normalized_name", None) or getattr(loc, "raw_name", None)
    year = None
    if hasattr(loc, "last_seen") and loc.last_seen:
        try:
            year = int(str(loc.last_seen)[:4])
        except Exception:
            pass

    logger.info(f"Suggesting coordinates for '{name}' (year={year})")
    # 1) Manual override
    fix = get_manual_fix(name)
    if fix:
        logger.info(f"Suggestion: manual for '{name}'")
        return {**fix, "source": "manual", "confidence": "manual"}

    # 2) Historical
    hist = lookup_historical(name, year)
    if hist:
        logger.info(f"Suggestion: historical for '{name}'")
        return {**hist, "source": "historical", "confidence": "medium"}

    # 3) Google
    google = call_google(name)
    if google:
        logger.info(f"Suggestion: google for '{name}'")
        return google

    # 4) Nominatim fallback
    nom = call_nominatim(name)
    if nom:
        logger.info(f"Suggestion: nominatim for '{name}'")
        return nom

    logger.warning(f"No suggestion found for '{name}'")
    return None
