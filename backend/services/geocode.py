#/Users/kingal/mapem/backend/services/geocode.py
"""Geocoding utilities with a plugin architecture."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

import requests

from backend.config import settings
from backend.models.location_models import LocationOut
from backend.services.geocode_brain import GazetteerDBGeocoder, GeoContext, RateLimiter
from pydantic import BaseModel
from backend.utils.helpers import calculate_name_similarity, normalize_location
from backend.utils.logger import get_file_logger
from backend import models

def extract_and_validate_coords(entry: dict[str, Any]) -> Tuple[float, float] | None:
    """Pull lat/lng from a dict and ensure they’re valid floats."""
    try:
        lat = float(entry.get("latitude") or entry.get("lat"))
        lng = float(entry.get("longitude") or entry.get("lng"))
        if lat is None or lng is None:
            return None
        return lat, lng
    except (TypeError, ValueError):
        return None

logger = get_file_logger("geocode")

DEFAULT_CACHE_PATH = Path(
    os.getenv("GEOCODE_CACHE_FILE", Path(__file__).resolve().parent / "geocode_cache.json")
)
FAIL_TTL_SECONDS = 3600  # 1 hour


class GeocodeError(BaseModel):
    """Model returned when geocoding fails."""

    raw_name: str
    message: str
    reason: str  # e.g. "cache‐expired", "manual‐missing", "all‐failed", etc.


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
        coords = extract_and_validate_coords(hit)
        if not coords:
            logger.warning("⚠️ Manual fix missing coords for '%s'", place)
            return None
        lat, lng = coords
        logger.info("🟧 Manual fix hit: %s", place)
        return LocationOut(
            raw_name=place,
            normalized_name=hit.get("normalized_name", place),
            latitude=lat,
            longitude=lng,
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
            logger.info("🟥 Cache miss for %s", place)
            return None
        try:
            if len(entry) == 4:
                lat, lng, norm, conf = entry
                src = "cache"
                status = "ok"
                label = src
                ts = 0.0
            elif len(entry) == 6 and isinstance(entry[5], (int, float)):
                lat, lng, norm, conf, src, ts = entry
                status = "ok"
                label = src
            elif len(entry) == 7:
                lat, lng, norm, conf, src, status, ts = entry
                label = src
            elif len(entry) >= 8:
                lat, lng, norm, conf, src, status, label, ts = entry[:8]
            else:
                raise ValueError("unexpected cache format")
        except Exception:
            logger.warning("🧯 Cache entry malformed for '%s': %s", key, entry)
            del geocode.cache[key]
            return None
        if lat is None and ts and (now - ts) > FAIL_TTL_SECONDS:
            logger.info("⏰ Cache expired for '%s'", place)
            del geocode.cache[key]
            return None
        if lat is None or lng is None:
            logger.info("🟥 Cache hit without coords for '%s'", place)
            return None
        logger.info("🟦 Cache hit for %s", place)
        return LocationOut(
            raw_name=place,
            normalized_name=norm,
            latitude=lat,
            longitude=lng,
            confidence_score=float(conf or 0.0),
            confidence_label=label,
            status=status,
            source=src,
         )


class HistoricalGeocoder:
    """Lookup old place names from a historical table."""

    def __init__(self, data: Optional[Dict[str, Any]] = None) -> None:
        self.data = {}
        for k, v in (data or {}).items():
            norm = normalize_location(k)
            key = (norm if norm is not None else k).lower()
            self.data[key] = v

    def resolve(self, geocode: "Geocode", session, place: str) -> Optional[LocationOut]:
        key = normalize_location(place)
        if key is None:
            key = place
        key = key.lower()
        hit = self.data.get(key)
        if not hit:
            return None
        coords = extract_and_validate_coords(hit)
        if not coords:
            logger.warning("⚠️ Manual fix missing coords for '%s'", place)
            return None
        lat, lng = coords
        logger.info("🟨 Historical fix hit: %s", place)
        return LocationOut(
            raw_name=place,
            normalized_name=hit.get("normalized_name", place),
            latitude=lat,
            longitude=lng,
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
        # Conservative provider limits (Nominatim: 1 rps per policy; Google generous default)
        self._google_limiter = RateLimiter(5.0)
        self._nominatim_limiter = RateLimiter(1.0)

    def resolve(self, geocode: "Geocode", session, place: str) -> Optional[LocationOut]:
        if geocode.mock_mode:
            logger.info("🛑 Mock mode active - skipping API call for '%s'", place)
            return None
        result = None
        # Google first if available
        if self.api_key:
            try:
                self._google_limiter.sleep_if_needed()
            except Exception:
                pass
            result = geocode._google(place)
        if not result:
            try:
                self._nominatim_limiter.sleep_if_needed()
            except Exception:
                pass
            result = geocode._nominatim_geocode(place)
        if not result:
            logger.info("❌ External API miss for '%s'", place)
            return None
        lat, lng, norm, conf, src = result
        if lat is None or lng is None:
            logger.info("❌ External API returned no coords for '%s'", place)
            return None
        logger.info("✅ %s geocode for '%s'", src, place)
        # Persist attempt with minimal raw I/O for reproducibility
        try:
            from backend.models.geocode_debug import GeocodeAttempt  # local import to avoid circular at import-time
            if session is not None:
                attempt = GeocodeAttempt(
                    raw_place=place,
                    name_norm=normalize_location(place) or place,
                    provider=src,
                    chosen="yes",
                    latitude=float(lat),
                    longitude=float(lng),
                    score=float(conf or 0.0),
                    request_json={"q": place, "provider": src},
                    response_json={"lat": lat, "lng": lng, "name": norm},
                )
                session.add(attempt)
                session.flush()
        except Exception:
            logger.exception("Failed to persist geocode attempt for '%s'", place)

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
        mock_mode: bool | None = None,
    ) -> None:
        self.api_key = api_key
        self.cache_file = Path(cache_file or DEFAULT_CACHE_PATH)
        self.cache_enabled = use_cache
        self.cache: Dict[str, Any] = self._load_cache() if use_cache else {}
        self.unresolved_logger = unresolved_logger
        self.mock_mode = bool(
            os.getenv("MAPEM_MOCK_GEOCODE", "0") == "1" if mock_mode is None else mock_mode
        )
        if not settings.ALLOW_GEOCODE_EXTERNAL:
            # If external geocoding is disabled, drop external plugin from chain
            pass

        self.manual_fixes = manual_fixes or {}
        self.historical_lookup = historical_lookup or {}

        self.plugins = [
            ManualOverrideGeocoder(self.manual_fixes),
            HistoricalGeocoder(self.historical_lookup),
            PermanentCacheGeocoder(),
            # Prefer local Gazetteer before external calls
            GazetteerDBGeocoder(),
        ]
        if settings.ALLOW_GEOCODE_EXTERNAL:
            self.plugins.append(ExternalAPIGeocoder(api_key))

    # ─── Cache helpers ─────────────────────────────────────────────
    def _load_cache(self) -> Dict[str, Any]:
        if self.cache_file.exists():
            try:
                cache = json.loads(self.cache_file.read_text())
                self.cache = cache
                self._prune_cache()
                return cache
            except json.JSONDecodeError:
                logger.warning("⚠️ Cache corrupted — starting fresh.")
        return {}

    def _save_cache(self) -> None:
        if self.cache_enabled:
            try:
                self._prune_cache()
                with self.cache_file.open("w") as f:
                    json.dump(self.cache, f, indent=2)
            except Exception as e:
                logger.error("❌ Could not save cache: %s", e)

    def _prune_cache(self) -> None:
        if not self.cache_enabled:
            return
        now = time.time()
        keys_to_delete = []
        for k, entry in list(self.cache.items()):
            try:
                ts = entry[5] if len(entry) >= 6 and isinstance(entry[5], (int, float)) else entry[-1]
                lat = entry[0]
            except Exception:
                logger.warning("⚠️ Removing malformed cache entry '%s': %s", k, entry)
                keys_to_delete.append(k)
                continue
            if lat is None and isinstance(ts, (int, float)) and (now - ts) > FAIL_TTL_SECONDS:
                keys_to_delete.append(k)
        for k in keys_to_delete:
            del self.cache[k]

    # ─── Normalization ────────────────────────────────────────────
    @staticmethod
    def _normalize_key(place: str) -> str:
        norm = normalize_location(place.strip())
        return norm.lower() if norm else place.strip().lower()

    # ─── Retry helper ─────────────────────────────────────────────
    def _retry(self, fn, *args, retries=2, backoff=1, **kwargs):
        last_exc = None
        for attempt in range(retries):
            try:
                return fn(*args, **kwargs)
            except requests.RequestException as e:
                last_exc = e
                logger.warning(
                    "⚠️ Request fail (%d/%d): %s", attempt + 1, retries, e
                )
                time.sleep(backoff * (2 ** attempt))
        logger.error("❌ Max retries exceeded: %s", last_exc)
        return None

    # ─── External providers ───────────────────────────────────────
    def _google(self, place: str):
        if not self.api_key:
            return None
        logger.info("🌐 Google geocode query for '%s'", place)
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
        logger.info("🌐 Nominatim geocode query for '%s'", place)
        resp = self._retry(
            requests.get,
            url,
            params=params,
            headers={
                "User-Agent": "MapEm/1.0 (contact: admin@mapem.app)",
                "Accept-Language": "en",
            },
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
    def get_or_create_location(self, session, place: str, *, event_year: int | None = None, admin_hint: str | None = None, family_coords: list[tuple[float, float]] | None = None) -> Optional[LocationOut | GeocodeError]:
        raw = place.strip()
        key = self._normalize_key(raw)
        now = time.time()
        logger.debug("🔍 geocode chain for: %s", raw)

        # Periodic cache prune (every 5 min)
        if self.cache_enabled and (now - getattr(self, "_last_prune", 0)) > 300:
            self._prune_cache()
            self._last_prune = now

        # Build shared context for era-aware scoring
        context = GeoContext(event_year=event_year, admin_hint=admin_hint, family_coords=family_coords)

        # Try each geocoder plugin in sequence
        for plugin in self.plugins:
            # GazetteerDBGeocoder has different signature that uses context
            if isinstance(plugin, GazetteerDBGeocoder):
                try:
                    result = plugin.resolve(session, raw, context=context, debug=True)
                except Exception:
                    logger.exception("❌ GazetteerDBGeocoder failed for '%s'", raw)
                    result = None
            else:
                result = plugin.resolve(self, session, raw)
            if result:
                # Cache successful lookups (unless from PermanentCacheGeocoder)
                if self.cache_enabled and not isinstance(plugin, PermanentCacheGeocoder):
                    self.cache[key] = {
                        "latitude": result.latitude,
                        "longitude": result.longitude,
                        "normalized": result.normalized_name,
                        "confidence": float(getattr(result, "confidence_score", 0.0)),
                        "source": getattr(result, "source", "unknown"),
                        "status": getattr(result, "status", "ok"),
                        "label": getattr(result, "confidence_label", getattr(result, "source", "unknown")),
                        "timestamp": now,
                    }
                    self._save_cache()
                # Ensure model has expected fields (defensive; Pydantic validates already)
                return result

        # No geocoder plugin found a result — cache the miss
        if self.cache_enabled:
            self.cache[key] = {
                "latitude": None,
                "longitude": None,
                "normalized": raw,
                "confidence": 0.0,
                "source": "geocoder",
                "status": "unresolved",
                "label": "geocoder",
                "timestamp": now,
            }
            self._save_cache()

        if self.unresolved_logger:
            self.unresolved_logger(place=raw, reason="geocoder-miss", details={})
        logger.warning("❌ Geocode miss for '%s'", raw)
        return GeocodeError(raw_name=raw, message="unresolved", reason="geocoder-miss")



GEOCODER = Geocode(api_key=settings.GOOGLE_MAPS_API_KEY)

__all__ = [
    "Geocode",
    "GEOCODER",
    "ManualOverrideGeocoder",
    "PermanentCacheGeocoder",
    "HistoricalGeocoder",
    "ExternalAPIGeocoder",
    "LocationOut",
    "GeocodeError",
]
