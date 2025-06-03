"""
LocationService  – central “place resolver” for MaPeM.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from backend.models.location_models import LocationOut
from backend.services.geocode import Geocode
from backend.services.location_processor import process_location
from backend.utils.log_utils import normalize_place

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _load_json(path: str) -> dict[str, dict]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _safe_lat(hit: dict) -> Optional[float]:
    return hit.get("lat") or hit.get("latitude")


def _safe_lng(hit: dict) -> Optional[float]:
    return hit.get("lng") or hit.get("longitude")


# ─────────────────────────────────────────────────────────────────────────────
# LocationService
# ─────────────────────────────────────────────────────────────────────────────
class LocationService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_file: str = "geocode_cache.json",
        use_cache: bool = True,
        data_dir: Optional[str] = None,
    ):
        self.data_dir = (
            data_dir
            or os.getenv("MAPEM_DATA_DIR")
            or os.path.join(os.path.dirname(__file__), "..", "data")
        )
        logger.debug("🔍 LocationService using data_dir=%s", self.data_dir)

        self.geocoder = Geocode(
            api_key=api_key, cache_file=cache_file, use_cache=use_cache
        )

        # ── Manual overrides ──────────────────────────────────────────────
        self.manual_fixes: dict[str, dict] = {}
        manual_path = os.path.join(self.data_dir, "manual_place_fixes.json")
        if os.path.exists(manual_path):
            try:
                for key, val in _load_json(manual_path).items():
                    nk = normalize_place(key) or key
                    self.manual_fixes[nk.lower()] = val
                logger.debug("📌 Loaded %d manual fixes", len(self.manual_fixes))
            except Exception as e:
                logger.warning("⚠️ Failed to load manual fixes: %s", e)

        # ── Historical lookup ─────────────────────────────────────────────
        self.historical_lookup: dict[str, dict] = {}
        hist_dir = os.path.join(self.data_dir, "historical_places")
        if os.path.isdir(hist_dir):
            for fname in os.listdir(hist_dir):
                if fname.endswith(".json"):
                    try:
                        for key, val in _load_json(os.path.join(hist_dir, fname)).items():
                            nk = normalize_place(key) or key
                            self.historical_lookup[nk.lower()] = val
                    except Exception as e:
                        logger.warning("⚠️ Failed to load history %s: %s", fname, e)
        logger.info("✅ Loaded %d historical records.", len(self.historical_lookup))

        # Unresolved output path
        self.unresolved_path = os.path.join(self.data_dir, "unresolved_locations.json")

    # ─────────────────────────────────────────────────────────────────────────
    # Main entry point
    # ─────────────────────────────────────────────────────────────────────────

    def _append_unresolved(
        self,
        raw_name: str,
        normalized_name: str,
        status: str,
        event_year: Optional[int],
        source_tag: str,
        tree_id: Optional[str] = None,       # 👈 add tree_id parameter
    ) -> None:
        """
        Write one JSON entry into unresolved_locations.json,
        now including tree_id so retry can pick it up.
        """
        payload = {
            "raw_name": raw_name,
            "normalized_name": normalized_name,
            "status": status,
            "event_year": event_year,
            "source_tag": source_tag,
            "tree_id": tree_id,               # 👈 include here
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            data = _load_json(self.unresolved_path) if os.path.exists(self.unresolved_path) else []
            data.append(payload)
            with open(self.unresolved_path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
        except Exception as ex:
            logger.error(f"❌ Could not write unresolved dump: {ex}")
            
            
            
            
            
    def resolve_location(
        self,
        raw_place: Optional[str],
        *,
        event_year: Optional[int] = None,
        source_tag: str = "",
        tree_id: Optional[str] = None,
    ) -> LocationOut:
        if not raw_place:
            return LocationOut(
                raw_name="",
                normalized_name="",
                latitude=None,
                longitude=None,
                confidence_score=0.0,
                status="empty",
                source="none",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        processed: LocationOut = process_location(
            raw_place=raw_place,
            event_year=event_year,
            source_tag=source_tag,
        )

        if processed.status == "vague" and event_year and event_year < 1890:
            logger.debug(f"🟡 Vague state pre-1890 override for '{raw_place}'")
            processed.status = "vague_state_pre1890"

        norm = processed.normalized_name or normalize_place(raw_place) or raw_place.lower().replace(" ", "_")
        key = norm.lower()

        hit = self.manual_fixes.get(key) or self.historical_lookup.get(key)
        if hit:
            return LocationOut(
                raw_name=raw_place,
                normalized_name=hit.get("normalized_name", norm),
                latitude=_safe_lat(hit),
                longitude=_safe_lng(hit),
                confidence_score=1.0,
                status=hit.get("status", "manual_override"),
                source=hit.get("source", "manual_or_historical"),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        geo: Optional[LocationOut] = None
        try:
            geo = self.geocoder.get_or_create_location(None, norm)
        except Exception as ex:
            logger.warning(f"⚠️ Geocode error for '{raw_place}': {ex}")

        if geo and geo.latitude is not None and geo.longitude is not None and (geo.latitude, geo.longitude) != (0.0, 0.0):
            return LocationOut(
                raw_name=raw_place,
                normalized_name=geo.normalized_name or norm,
                latitude=geo.latitude,
                longitude=geo.longitude,
                confidence_score=geo.confidence_score or 0.5,
                status="ok",
                source=geo.source or "external",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        if (
            geo
            and (geo.latitude, geo.longitude) == (0.0, 0.0)
            and event_year and event_year < 1890
            and "mississippi" in norm.lower()
        ):
            logger.debug("🟠 Overriding to vague_state_pre1890 based on 0,0 coords + year<1890")
            return LocationOut(
                raw_name=raw_place,
                normalized_name=norm,
                latitude=0.0,
                longitude=0.0,
                confidence_score=0.5,
                status="vague_state_pre1890",
                source=geo.source or "external",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        logger.warning(f"🚫 UNRESOLVED '{raw_place}' (status={processed.status})")
        self._append_unresolved(
            raw_name=raw_place,
            normalized_name=norm,
            status=processed.status,
            event_year=event_year,
            source_tag=source_tag,
            tree_id=tree_id,
        )

        return LocationOut(
            raw_name=raw_place,
            normalized_name=norm,
            latitude=None,
            longitude=None,
            confidence_score=0.0,
            status="unresolved",
            source="none",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


# End of LocationService class

logger.debug(
    "✅ LocationService loaded with resolve_location=%s",
    hasattr(LocationService, "resolve_location"),
)
