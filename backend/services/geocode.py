"""Geocoding utilities with a plugin architecture."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from backend.config import settings
from backend.models.location_models import LocationOut
from backend.utils.helpers import calculate_name_similarity, normalize_location
from backend.utils.logger import get_file_logger
from backend import models


logger = get_file_logger("geocode")

DEFAULT_CACHE_PATH = Path(
    os.getenv("GEOCODE_CACHE_FILE", Path(__file__).resolve().parent / "geocode_cache.json")
)
FAIL_TTL_SECONDS = 3600  # 1 hour


class ManualOverrideGeocoder:
    """Return coordinates from a supplied override table."""

    def __init__(self, fixes: Optional[Dict[str, Any]] = None) -> None:
        self.fixes: Dict[str, Any] = {}
        for key, val in (fixes or {}).items():
            norm = normalize_location(key) or key
            self.fixes[norm.lower()] = val

    def resolve(self, geocode: "Geocode", session, place: str) -> Optional[LocationOut]:
        norm = normalize_location(place) or place
        key = norm.lower()
        hit = self.fixes.get(key)
        if not hit:
            return None
        logger.info("🟧 Manual fix hit: %s", place)
        return LocationOut(
            raw_name=place,
            normalized_name=hit.get("normalized_name", place),
            latitude=hit.get("latitude") or hit.get("lat"),
            longitude=hit.get("longitude") or hit.get("lng"),
            confidence_score=1.0,
            confidence_label="manual",
            status="manual",
            source="manual",
        )


class PermanentCacheGeocoder:
    """Retrieve previously resolved coordinates from the cache."""

    def resolve(self, geocode: "Geocode", session, place: str) -> Optional[LocationOut]:
        if not geocode.cache_enabled:
            return None
        key = geocode._normalize_key(place)
        now = time.time()
        entry = geocode.cache.get(key)
        if not entry:
            return None
        try:
            lat, lng, norm, conf, src, ts = entry
        except Exception:
            logger.warning("🧯 Cache entry malformed for '%s': %s", key, entry)
            return None
        if lat is None and (now - ts) > FAIL_TTL_SECONDS:
            del geocode.cache[key]
            return None
        if lat is None or lng is None:
            return None
        logger.info("🟦 Cache hit for %s", place)
        return LocationOut(
            raw_name=place,
            normalized_name=norm,
            latitude=lat,
            longitude=lng,
            confidence_score=float(conf or 0.0),
            confidence_label=src,
            status="ok",
            source=src,
        )


class HistoricalGeocoder:
    """Lookup old place names from a historical table."""

    def __init__(self, data: Optional[Dict[str, Any]] = None) -> None:
        self.data = {
            (normalize_location(k) if normalize_location(k) is not None else k): v
            for k, v in (data or {}).items()
        }

    def resolve(self, geocode: "Geocode", session, place: str) -> Optional[LocationOut]:
        key = normalize_location(place)
        hit = self.data.get(key)
        if not hit:
            return None
        logger.info("🟨 Historical fix hit: %s", place)
        return LocationOut(
            raw_name=place,
            normalized_name=hit.get("normalized_name", place),
            latitude=hit.get("latitude") or hit.get("lat"),
            longitude=hit.get("longitude") or hit.get("lng"),
            confidence_score=0.85,
            confidence_label="historical",
            status="ok",
            source="historical",
        )


class FuzzyAliasGeocoder:
    """Simple DB based fuzzy matcher."""

    def resolve(self, geocode: "Geocode", session, place: str) -> Optional[LocationOut]:
        if not session:
            return None
        raw = place.strip()
        try:
            existing = (
                session.query(models.Location)
                .filter(models.Location.raw_name == raw)
                .one_or_none()
            )
            if existing:
                logger.debug("🟢 DB exact match for %s", raw)
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
            db_locs = session.query(models.Location).all()
            for loc in db_locs:
                compare_to = loc.normalized_name or loc.raw_name
                sim = calculate_name_similarity(compare_to, raw)
                if sim >= 90 and loc.latitude and loc.longitude:
                    logger.info("🟪 DB fuzzy match for '%s' ≈ '%s' (%.1f%%)", raw, compare_to, sim)
                    return LocationOut(
                        raw_name=raw,
                        normalized_name=loc.normalized_name or loc.raw_name,
                        latitude=loc.latitude,
                        longitude=loc.longitude,
                        confidence_score=float(loc.confidence_score or 0.8),
                        confidence_label="db-fuzzy",
                        status="ok",
                        source="db-fuzzy",
                    )
        except Exception:
            logger.exception("❌ DB lookup failed for %s", raw)
        return None


class ExternalAPIGeocoder:
    """Use external providers (Google / Nominatim)."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    def resolve(self, geocode: "Geocode", session, place: str) -> Optional[LocationOut]:
        result = geocode._google(place) or geocode._nominatim_geocode(place)
        if not result:
            return None
        lat, lng, norm, conf, src = result
        logger.info("✅ %s geocode for '%s'", src, place)
        return LocationOut(
            raw_name=place,
            normalized_name=norm,
            latitude=lat,
            longitude=lng,
            confidence_score=float(conf or 0.0),
            confidence_label=src,
            status="ok",
            source=src,
        )


class Geocode:
    """Chain plugins to resolve a place string."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_file: Optional[str | Path] = None,
        use_cache: bool = True,
        manual_fixes: Optional[Dict[str, Any]] = None,
        historical_lookup: Optional[Dict[str, Any]] = None,
        unresolved_logger=None,
    ) -> None:
        self.api_key = api_key
        self.cache_file = Path(cache_file or DEFAULT_CACHE_PATH)
        self.cache_enabled = use_cache
        self.cache: Dict[str, Any] = self._load_cache() if use_cache else {}
        self.unresolved_logger = unresolved_logger

        self.manual_fixes = manual_fixes or {}
        self.historical_lookup = historical_lookup or {}

        self.plugins = [
            ManualOverrideGeocoder(self.manual_fixes),
            PermanentCacheGeocoder(),
            HistoricalGeocoder(self.historical_lookup),
            FuzzyAliasGeocoder(),
            ExternalAPIGeocoder(api_key),
        ]

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
    @staticmethod
    def _normalize_key(place: str) -> str:
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

    def _nominatim_geocode(self, place: str):
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
        logger.debug("🔍 geocode chain for: %s", raw)

        for plugin in self.plugins:
            result = plugin.resolve(self, session, raw)
            if result:
                if self.cache_enabled and not isinstance(plugin, PermanentCacheGeocoder):
                    self.cache[key] = [
                        result.latitude,
                        result.longitude,
                        result.normalized_name,
                        result.confidence_score,
                        result.source,
                        now,
                    ]
                    self._save_cache()
                return result

        # No result
        if self.cache_enabled:
            self.cache[key] = [None, None, raw, 0.0, "geocoder", now]
            self._save_cache()
        if self.unresolved_logger:
            self.unresolved_logger(place=raw, reason="geocoder-miss", details={})
        logger.warning("❌ Geocode miss for '%s'", raw)
        return None


GEOCODER = Geocode(api_key=settings.GOOGLE_MAPS_API_KEY)

__all__ = [
    "Geocode",
    "GEOCODER",
    "ManualOverrideGeocoder",
    "PermanentCacheGeocoder",
    "HistoricalGeocoder",
    "FuzzyAliasGeocoder",
    "ExternalAPIGeocoder",
    "LocationOut",
]
