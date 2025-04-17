#os.path.expanduser("~")/mapem/backend/services/geocode.py
import os
import json
import time
import requests
import logging
from datetime import datetime
from urllib.parse import urlencode
from backend import models
from backend.utils.helpers import normalize_location_name, calculate_name_similarity, normalize_confidence_score

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Load manual overrides from JSON (if available)
MANUAL_FIXES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "manual_place_fixes.json")
if os.path.exists(MANUAL_FIXES_FILE):
    with open(MANUAL_FIXES_FILE, "r") as f:
        try:
            manual_fixes = json.load(f)
        except Exception:
            manual_fixes = {}
else:
    manual_fixes = {}

# Placeholder for historical lookup: load from your historical_places JSON files if needed.
historical_lookup = {}
# Example: historical_lookup["sunflower:beat 2, sunflower county, mississippi"] = {
#   "modern_equivalent": "Ruleville, Sunflower County, Mississippi, USA",
#   "lat": 33.7879,
#   "lng": -90.5764,
#   "year_range": "1900-1930"
# }

print(f"🛠️ Loaded geocode.py from: {__file__}")

# Helper function to classify unresolved locations
def classify_location_failure(raw_name):
    generic = {"mississippi", "usa", "tennessee", "louisiana", "unknown"}
    normalized = raw_name.lower().strip()
    if normalized in generic:
        return "too_vague", None
    if ", ," in raw_name or raw_name.startswith(",") or raw_name.endswith(","):
        return "format_error", None
    if "boliver" in normalized:
        return "typo_or_misspelling", "Bolivar County, Mississippi, USA"
    if "moorehead" in normalized:
        return "typo_or_misspelling", "Moorhead, Sunflower, Mississippi, USA"
    # Add additional patterns if needed...
    return "geocode_failed", None

class Geocode:
    def __init__(self, api_key=None, cache_file='geocode_cache.json', use_cache=True):
        self.api_key = api_key
        self.cache_file = cache_file
        self.cache_enabled = use_cache
        self.cache = self._load_cache() if use_cache else {}

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning("⚠️ Cache file corrupted, starting fresh.")
                return {}
        return {}

    def _save_cache(self):
        if self.cache_enabled:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)

    def _normalize_key(self, place):
        return normalize_location_name(place.strip()).lower()

    def _retry_request(self, func, *args, retries=2, backoff=1, **kwargs):
        for attempt in range(1, retries + 1):
            try:
                return func(*args, **kwargs)
            except requests.RequestException as e:
                logger.warning(f"⚠️ Request failed (attempt {attempt}/{retries}): {e}")
                time.sleep(backoff * attempt)
        return None

    def _google_geocode(self, location):
        base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": location, "key": self.api_key}
        url = f"{base_url}?{urlencode(params)}"
        def call():
            return requests.get(url, timeout=5)
        resp = self._retry_request(call)
        if not resp or resp.status_code != 200:
            logger.error(f"❌ Google geocode error: status {resp.status_code if resp else 'no response'}")
            return None, None, None, None
        data = resp.json()
        if not data.get('results'):
            return None, None, None, None
        result = data['results'][0]
        loc = result['geometry']['location']
        location_type = result['geometry'].get('location_type', '')
        # Map to numeric confidence: if rooftop, 1.0; otherwise 0.75.
        confidence = 1.0 if location_type.upper() == "ROOFTOP" else 0.75
        normalized_name = result.get('formatted_address', location)
        return loc['lat'], loc['lng'], normalized_name, confidence

    def _nominatim_geocode(self, location):
        base_url = "https://nominatim.openstreetmap.org/search"
        headers = {"User-Agent": "GenealogyMapper"}
        params = {"q": location, "format": "json", "limit": 1}
        def call(p):
            return requests.get(base_url, params=p, headers=headers, timeout=10)
        resp = self._retry_request(call, params)
        if resp and resp.status_code == 200:
            data = resp.json()
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                name = data[0]['display_name']
                return lat, lon, name, 0.8
        # Fallback: try only the city part
        city = location.split(",")[0].strip()
        logger.info(f"🪃 Falling back to city-only geocode: '{city}'")
        params["q"] = city
        resp = self._retry_request(call, params)
        if resp and resp.status_code == 200:
            data = resp.json()
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                name = data[0]['display_name']
                return lat, lon, name, 0.7
        return None, None, None, None

    def preload_cache(self, place_list):
        """Bulk-geocode a list of places to warm the cache."""
        for place in set(place_list):
            key = self._normalize_key(place)
            if key in self.cache:
                continue
            logger.info(f"🔄 Preloading geocode for '{place}'")
            if self.api_key:
                lat, lng, norm, conf = self._google_geocode(place)
            else:
                lat, lng, norm, conf = self._nominatim_geocode(place)
            if lat is not None:
                self.cache[key] = (lat, lng, norm, conf)
        self._save_cache()

    def get_or_create_location(self, session, location_name):
        logger.debug(f"Geocode called with place='{location_name}'")
        if not location_name:
            logger.warning("⚠️ Empty location_name provided.")
            return None

        raw_name = location_name.strip().replace(",,", ",").replace("  ", " ")
        key = self._normalize_key(raw_name)

        # 🔁 Manual override
        if raw_name in manual_fixes:
            override = manual_fixes[raw_name]
            # For manual overrides, we force a valid numeric score:
            conf = 1.0  # or any appropriate numeric value
            conf_label = "manual"
            return {
                "raw_name": raw_name,
                "name": override.get("modern_equivalent", raw_name),
                "normalized_name": override.get("modern_equivalent", raw_name),
                "latitude": override.get("lat"),
                "longitude": override.get("lng"),
                "confidence_score": float(conf),
                "confidence_label": conf_label,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "manual",
                "source": "manual",
                "historical_data": {}
            }

        # 🔁 Historical match
        hist_key = f"sunflower:{raw_name.lower()}"
        if hist_key in historical_lookup:
            hp = historical_lookup[hist_key]
            conf = 1.0
            conf_label = "historical"
            return {
                "raw_name": raw_name,
                "name": hp.get("modern_equivalent", raw_name),
                "normalized_name": hp.get("modern_equivalent", raw_name),
                "latitude": hp.get("lat"),
                "longitude": hp.get("lng"),
                "confidence_score": float(conf),
                "confidence_label": conf_label,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "historical",
                "source": "historical",
                "historical_data": {"year_range": hp.get("year_range")}
            }

        # 🔁 Vague place
        if raw_name.lower() in {"mississippi", "usa", "unknown"}:
            conf = 0.0  # Force a numeric 0.0 for vague locations
            conf_label = "unknown"
            return {
                "raw_name": raw_name,
                "name": raw_name,
                "normalized_name": raw_name,
                "latitude": None,
                "longitude": None,
                "confidence_score": float(conf),
                "confidence_label": conf_label,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "vague",
                "source": "none",
                "historical_data": {}
            }

        # 🔁 Cache hit
        if self.cache_enabled and key in self.cache:
            lat, lng, norm, conf = self.cache[key]
            conf_label = "cache"  # explicitly set label for cached entries
            # Ensure conf is a float
            conf = float(conf or 0.0)
            return {
                "raw_name": raw_name,
                "name": norm,
                "normalized_name": norm,
                "latitude": lat,
                "longitude": lng,
                "confidence_score": conf,
                "confidence_label": conf_label,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "ok",
                "source": "cache",
                "historical_data": {}
            }

        # 🔁 Fuzzy DB match
        if session:
            for loc in session.query(models.Location).all():
                sim = calculate_name_similarity(loc.name, raw_name)
                if sim >= 90:
                    return {
                        "raw_name": raw_name,
                        "name": loc.name,
                        "normalized_name": loc.normalized_name,
                        "latitude": loc.latitude,
                        "longitude": loc.longitude,
                        "confidence_score": float(loc.confidence_score or 0.0),
                        "confidence_label": loc.confidence_label,
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": "ok",
                        "source": "db",
                        "historical_data": loc.historical_data or {}
                    }

        # 🔁 External geocode fallback
        if self.api_key:
            lat, lng, norm, conf = self._google_geocode(raw_name)
            source = "google"
        else:
            lat, lng, norm, conf = self._nominatim_geocode(raw_name)
            source = "nominatim"

        if lat is None or lng is None:
            category, suggested_fix = classify_location_failure(raw_name)
            unresolved_file = os.path.join(os.path.dirname(__file__), "..", "data", "unresolved_locations.json")
            unresolved = []
            if os.path.exists(unresolved_file):
                try:
                    with open(unresolved_file, "r") as uf:
                        unresolved = json.load(uf)
                except Exception:
                    unresolved = []
            unresolved.append({
                "raw_name": raw_name,
                "source_tag": "unknown",
                "timestamp": datetime.utcnow().isoformat(),
                "reason": category,
                "status": "manual_fix_pending",
                "suggested_fix": suggested_fix
            })
            with open(unresolved_file, "w") as uf:
                json.dump(unresolved, uf, indent=2)

            conf = 0.0
            conf_label = "unknown"

            return {
                "raw_name": raw_name,
                "name": raw_name,
                "normalized_name": raw_name,
                "latitude": None,
                "longitude": None,
                "confidence_score": float(conf),
                "confidence_label": conf_label,
                "timestamp": datetime.utcnow().isoformat(),
                "status": category,
                "source": "none",
                "historical_data": {}
            }

        # 🔁 Final success return
        # Ensure that conf is a float; if it's a string by any chance, force it to 0.0
        conf_label = None  # define a default at the star
        if isinstance(conf, str):
            conf_label = conf
            conf = 0.0
        else:
            conf = float(conf or 0.0)
            # If no specific label, we can mark it as numeric or leave it blank
            if conf > 0:
                conf_label = "numeric"
            else:
                conf_label = "unknown"
        conf_label = conf_label if conf_label is not None else "unknown"
        if self.cache_enabled:
            self.cache[key] = (lat, lng, norm, conf)
            self._save_cache()
        return {
            "raw_name": raw_name,
            "name": norm,
            "normalized_name": norm,
            "latitude": lat,
            "longitude": lng,
            "confidence_score": conf,
            "confidence_label": conf_label,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "ok",
            "source": source,
            "historical_data": {}
        }


if __name__ == "__main__":
    import sys
    place = " ".join(sys.argv[1:])
    print(f"\n📍 Geocoding test mode: {place}\n")

    from backend.services.geocode import Geocode
    from backend.utils.helpers import print_json

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    geocoder = Geocode(api_key=api_key)

    # Pass None for the DB session if not using DB inserts
    result = geocoder.get_or_create_location(None, place)

    print_json(result)
