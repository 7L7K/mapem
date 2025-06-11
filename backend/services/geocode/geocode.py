"""
Thin wrapper around Google + Nominatim geocoders,
with disk-based caching, fuzzy DB matching, TTL for failures,
manual/historical fixes, and robust logging.
"""

from __future__ import annotations
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlencode

import requests

from backend.config import settings, DATA_DIR
from backend.models.location_models import LocationOut
from backend.utils.helpers import normalize_location, calculate_name_similarity
from backend.utils.logger import get_file_logger
from backend import models

logger = get_file_logger("geocode")

DEFAULT_CACHE_PATH = Path(
    os.getenv(
        "GEOCODE_CACHE_FILE",
        DATA_DIR / "permanent_geocodes.json",
    )
)
FAIL_TTL_SECONDS = 3600  # 1 hour

class Geocode:
    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_file: Optional[str | Path] = None,
        use_cache: bool = True,
        manual_fixes: Optional[Dict[str, Any]] = None,
        historical_lookup: Optional[Dict[str, Any]] = None,
        unresolved_logger=None,  # Should be a callable, e.g. log_unresolved_location
    ):
        self.api_key = api_key
        self.cache_file = Path(cache_file or DEFAULT_CACHE_PATH)
        self.cache_enabled = use_cache
        self.cache: Dict[str, Any] = self._load_cache() if use_cache else {}
        self.manual_fixes = manual_fixes or {}
        self.historical_lookup = historical_lookup or {}
        self.unresolved_logger = unresolved_logger

        logger.debug("🧪 Geocoder initialized; cache_enabled=%s, manual_fixes=%s, historical_lookup=%s", 
                     use_cache, bool(self.manual_fixes), bool(self.historical_lookup))

    # ─── Cache helpers ─────────────────────────────────────────────
    def _load_cache(self) -> Dict[str, Any]:
        if self.cache_file.exists():
            try:
                return json.loads(self.cache_file.read_text())
            except json.JSONDecodeError:
                logger.warning("⚠️ Cache corrupted — starting fresh.")
        return {}

    def _save_cache(self) -> None:
        if self.cache_enabled:
            try:
                with self.cache_file.open("w") as f:
                    json.dump(self.cache, f, indent=2)
            except Exception as e:
                logger.error("❌ Could not save cache: %s", e)

    # ─── Normalization ────────────────────────────────────────────
    def _normalize_key(self, place: str) -> str:
        norm = normalize_location(place.strip())
        return norm.lower() if norm else place.strip().lower()

    # ─── Retry helper ─────────────────────────────────────────────
    def _retry(self, fn, *args, retries=2, backoff=1, **kwargs):
        for attempt in range(1, retries + 1):
            try:
                return fn(*args, **kwargs)
            except requests.RequestException as e:
                logger.warning("⚠️ Request fail (%d/%d): %s", attempt, retries, e)
                time.sleep(backoff * attempt)
        return None

    # ─── External providers ───────────────────────────────────────
    def _google(self, place: str):
        if not self.api_key:
            return None
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        q = urlencode({"address": place, "key": self.api_key})
        resp = self._retry(requests.get, f"{url}?{q}", timeout=5)
        if not resp or resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("status") != "OK" or not data["results"]:
            return None
        res = data["results"][0]
        loc = res["geometry"]["location"]
        confidence = 1.0 if res["geometry"].get("location_type") == "ROOFTOP" else 0.75
        return loc["lat"], loc["lng"], res.get("formatted_address", place), confidence, "google"

    def _nominatim(self, place: str):
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": place, "format": "json", "limit": 1}
        resp = self._retry(
            requests.get,
            url,
            params=params,
            headers={"User-Agent": "GenealogyMapper"},
            timeout=10,
        )
        if not resp or resp.status_code != 200:
            return None
        items = resp.json()
        if not items:
            return None
        lat = float(items[0]["lat"])
        lng = float(items[0]["lon"])
        name = items[0]["display_name"]
        return lat, lng, name, 0.8, "nominatim"

    # ─── Main entry ───────────────────────────────────────────────
    def get_or_create_location(self, session, place: str) -> Optional[LocationOut]:
        raw = place.strip()
        key = self._normalize_key(raw)
        now = time.time()
        logger.debug("🔍 geocode: raw=%r key=%r", raw, key)

        # 0. Manual fixes (hard override)
        if self.manual_fixes and key in self.manual_fixes:
            mf = self.manual_fixes[key]
            logger.info("🟧 Manual fix hit: %r → %r", raw, mf)
            return LocationOut(
                raw_name=raw,
                normalized_name=mf.get("normalized_name", raw),
                latitude=mf["latitude"],
                longitude=mf["longitude"],
                confidence_score=1.0,
                confidence_label="manual",
                status="ok",
                source="manual",
            )

        # 0.5 Historical lookup
        if self.historical_lookup and key in self.historical_lookup:
            hist = self.historical_lookup[key]
            logger.info("🟨 Historical fix hit: %r → %r", raw, hist)
            return LocationOut(
                raw_name=raw,
                normalized_name=hist.get("normalized_name", raw),
                latitude=hist["latitude"],
                longitude=hist["longitude"],
                confidence_score=0.85,
                confidence_label="historical",
                status="ok",
                source="historical",
            )

        # 1. Cache check
        if self.cache_enabled and key in self.cache:
            entry = self.cache[key]
            try:
                lat, lng, norm, conf, src, ts = entry
            except Exception as e:
                logger.warning("🧯 Cache entry for '%s' malformed (%s): %s", key, len(entry), entry)
                lat = lng = conf = ts = None
                norm = raw
                src = "cache-legacy"
                if len(entry) >= 2:
                    lat, lng = entry[0], entry[1]
                if len(entry) >= 3:
                    norm = entry[2]
                if len(entry) >= 4:
                    conf = entry[3]
                ts = now
                self.cache[key] = [lat, lng, norm, conf, src, ts]
                self._save_cache()

            # Purge old failed
            if lat is None and (now - ts) > FAIL_TTL_SECONDS:
                logger.info("🗑️ Expired failed cache entry for '%s'", key)
                del self.cache[key]
            else:
                logger.info("🟦 Cache hit (%s)", src)
                if lat is None or lng is None:
                    # Optional: log unresolved
                    if self.unresolved_logger:
                        self.unresolved_logger(place=raw, reason="cache-fail", details=entry)
                    return None
                return LocationOut(
                    raw_name=raw,
                    normalized_name=norm,
                    latitude=lat,
                    longitude=lng,
                    confidence_score=float(conf or 0.0),
                    confidence_label=src,
                    status="ok",
                    source=src,
                )

        # 2. DB exact + fuzzy match
        matched_loc = None
        if session:
            try:
                # Exact match on raw_name first
                existing = (
                    session
                    .query(models.Location)
                    .filter(models.Location.raw_name == raw)
                    .one_or_none()
                )
                if existing:
                    logger.debug("🟢 DB exact match: %r → (%.6f, %.6f)", raw, existing.latitude, existing.longitude)
                    return LocationOut(
                        raw_name=existing.raw_name,
                        normalized_name=existing.normalized_name,
                        latitude=existing.latitude,
                        longitude=existing.longitude,
                        confidence_score=float(existing.confidence_score or 1.0),
                        confidence_label="db",
                        status="ok",
                        source="db",
                    )
                # Fuzzy match on normalized_name (90%+)
                else:
                    # Check all similar locations (usually <10k, so safe)
                    db_locs = session.query(models.Location).all()
                    for loc in db_locs:
                        compare_to = loc.normalized_name or loc.raw_name
                        sim = calculate_name_similarity(compare_to, raw)
                        if sim >= 90 and loc.latitude and loc.longitude:
                            logger.info("🟪 DB fuzzy match for '%s' ≈ '%s' (%.1f%%)", raw, compare_to, sim)
                            matched_loc = loc
                            break
                    if matched_loc:
                        return LocationOut(
                            raw_name=raw,
                            normalized_name=matched_loc.normalized_name or matched_loc.raw_name,
                            latitude=matched_loc.latitude,
                            longitude=matched_loc.longitude,
                            confidence_score=float(matched_loc.confidence_score or 0.8),
                            confidence_label="db-fuzzy",
                            status="ok",
                            source="db-fuzzy",
                        )
            except Exception as e:
                logger.exception("❌ DB lookup failed for %r: %s", raw, e)

        # 3. External geocoder (Google/Nominatim)
        try:
            result = self._google(raw) or self._nominatim(raw)
            if result:
                lat, lng, norm, conf, src = result
            else:
                raise ValueError("Geocoder returned None")
        except Exception as e:
            logger.warning("❌ Geocode MISS '%s': %s", raw, e)
            lat = lng = conf = None
            norm = raw
            src = "geocoder"

        # 4. Cache it (always cache result even if fail, for TTL expiry)
        if self.cache_enabled:
            self.cache[key] = [lat, lng, norm, conf, src, now]
            self._save_cache()

        # 5. Final decision & unresolved logging
        if lat is None or lng is None:
            logger.warning("❌ Final Geocode MISS '%s'", raw)
            if self.unresolved_logger:
                self.unresolved_logger(place=raw, reason="geocoder-miss", details={"src": src})
            return None

        logger.info("✅ Geocode %s '%s' → (%s,%s)", src, raw, lat, lng)
        return LocationOut(
            raw_name=raw,
            normalized_name=norm,
            latitude=lat,
            longitude=lng,
            confidence_score=float(conf or 0.0),
            confidence_label=src,
            status="ok",
            source=src,
        )

# Singleton instance for the app
GEOCODER = Geocode(api_key=settings.GOOGLE_MAPS_API_KEY)

