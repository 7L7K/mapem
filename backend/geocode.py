# geocode.py
import os
import json
import time
import requests
from urllib.parse import urlencode
from backend import models
from backend.utils import normalize_location_name

print(f"🛠️ Loaded geocode.py from: {__file__}")

class Geocode:
    def __init__(self, api_key=None, cache_file='geocode_cache.json'):
        self.api_key = api_key
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def _save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)

    def _google_geocode(self, location):
        base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": location, "key": self.api_key}
        url = f"{base_url}?{urlencode(params)}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    result = data['results'][0]
                    loc = result['geometry']['location']
                    location_type = result['geometry'].get('location_type', '')
                    confidence = 1.0 if location_type.upper() == "ROOFTOP" else 0.75
                    normalized_name = result['formatted_address']
                    return loc['lat'], loc['lng'], normalized_name, confidence
        except Exception as e:
            print(f"Google Maps geocoding error: {e}")
        return None, None, None, None

    def lookup_geocode(self, location_name):
        """Unified lookup used by force_geocode to hit Nominatim or Google directly (without cache)."""
        if self.api_key:
            lat, lng, norm, conf = self._google_geocode(location_name)
        else:
            lat, lng, norm, conf = self._nominatim_geocode(location_name)

        if lat is not None and lng is not None:
            return {
                "lat": lat,
                "lng": lng,
                "confidence": conf
            }
        return None

    def force_geocode(self, place_str):
        """Bypass the cache and force a direct API lookup (used when location exists but has no coords)."""
        print(f"📡 Force geocoding: {place_str}")
        result = self.lookup_geocode(place_str)  # this should call your raw API fetch (Google/Nominatim)
        if result:
            return (
                result.get("lat"),
                result.get("lng"),
                normalize_location_name(place_str),
                result.get("confidence", 1.0),
            )
        return None, None, normalize_location_name(place_str), None

    def _nominatim_geocode(self, location):
        print(f"🌐 Querying Nominatim for: {location}")
        base_url = "https://nominatim.openstreetmap.org/search"
        headers = {"User-Agent": "GenealogyMapper"}
        params = {"q": location, "format": "json", "limit": 1}

        def query(params):
            try:
                resp = requests.get(base_url, params=params, headers=headers, timeout=10)
                print(f"🔁 Status {resp.status_code} for '{params['q']}'")
                data = resp.json()
                print(f"🧾 Raw data: {data}")
                if data:
                    lat = float(data[0]['lat'])
                    lon = float(data[0]['lon'])
                    name = data[0]['display_name']
                    return lat, lon, name, 0.8
            except Exception as e:
                print(f"🚨 Nominatim exception: {e}")
            return None, None, None, None

        # 1) Try full query
        lat, lon, name, conf = query(params)
        if lat is not None and lon is not None:
            return lat, lon, name, conf

        # 2) Fallback: just the city name
        city = location.split(",")[0].strip()
        print(f"🪃 Falling back to: {city}")
        params["q"] = city
        return query(params)
    def get_or_create_location(self, session, location_name):
        if not location_name:
            return None, None, None, None

        print(f"🔍 Looking up: {location_name}")

        # Check cache first
        if location_name in self.cache:
            print("⚡ Cache hit")
            return self.cache[location_name]

        # Fuzzy matching in DB
        from backend.utils import calculate_name_similarity
        existing_locations = session.query(models.Location).all()
        for loc in existing_locations:
            similarity = calculate_name_similarity(loc.name, location_name)
            print(f"🧪 Similarity with {loc.name} = {similarity}")
            if similarity >= 90:
                print("✅ DB Match found")
                return loc.latitude, loc.longitude, loc.normalized_name, loc.confidence_score

        print("🌐 Falling back to geocoding service...")

        if self.api_key:
            lat, lng, norm_name, conf = self._google_geocode(location_name)
        else:
            lat, lng, norm_name, conf = self._nominatim_geocode(location_name)

        if lat is not None and lng is not None:
            self.cache[location_name] = (lat, lng, norm_name, conf)
            self._save_cache()
            return lat, lng, norm_name, conf

        print("❌ Geocoding failed")
        return None, None, None, None

