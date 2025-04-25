# backend/services/location_service.py
import os
import json
import logging
from datetime import datetime
from typing import Optional

from backend.services.location_processor import process_location
from backend.services.geocode import Geocode
from backend.utils.log_utils import normalize_place
from backend.models.location_models import LocationOut
from backend.utils.helpers import normalize_confidence_score, log_unresolved_location

logger = logging.getLogger(__name__)

# NEW: central unresolved dump
UNRESOLVED_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "unresolved_locations.json"
)

class LocationService:
    def __init__(self, api_key=None, cache_file="geocode_cache.json", use_cache=True):
        self.geocoder = Geocode(api_key=api_key, cache_file=cache_file, use_cache=use_cache)

        # ---------------- Manual fixes ----------------
        manual_fixes_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "manual_place_fixes.json"
        )
        if os.path.exists(manual_fixes_path):
            with open(manual_fixes_path) as f:
                try:
                    fixes = json.load(f)
                except Exception:
                    fixes = {}
        else:
            fixes = {}
        self.manual_fixes = {normalize_place(k).lower(): v for k, v in fixes.items()}

        # ---------------- Historical lookup ----------------
        self.historical_lookup = {}
        historical_dir = os.path.join(
            os.path.dirname(__file__), "..", "data", "historical_places"
        )
        if os.path.exists(historical_dir):
            for fname in os.listdir(historical_dir):
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(historical_dir, fname)) as f:
                            data = json.load(f)
                            for k, v in data.items():
                                self.historical_lookup[normalize_place(k).lower()] = v
                    except Exception as e:
                        logger.warning(f"Could not load historical mapping {fname}: {e}")
        logger.info(f"Loaded {len(self.historical_lookup)} historical records.")

    # ---------- NEW helper ----------
    def _dump_unresolved(self, payload: dict):
        """Append to unresolved_locations.json so we can fix later."""
        try:
            if os.path.exists(UNRESOLVED_PATH):
                with open(UNRESOLVED_PATH) as f:
                    data = json.load(f)
            else:
                data = []
            data.append(payload)
            with open(UNRESOLVED_PATH, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write unresolved_locations.json: {e}")

    def resolve_location(
        self, raw_place: Optional[str], event_year=None, source_tag=""
    ) -> LocationOut:
        """
        Return a LocationOut object even when we can't get lat/lng,
        and always log/debug when something fails.
        """
        if not raw_place:
            return LocationOut(
                raw_name="",
                normalized_name="",
                latitude=None,
                longitude=None,
                confidence_score=0.0,
                status="empty",
                source="none",
                timestamp=datetime.utcnow().isoformat(),
            )

        # --- 1. preprocess / classify -----------------
        processed = process_location(
            raw_place, source_tag=source_tag, event_year=event_year
        ) or {
            "normalized": "",
            "status": "unknown",
            "confidence": 0.0,
            "fallback": None,
        }
        norm = processed.get("normalized") or ""
        fallback = processed.get("fallback")
        status = processed.get("status", "unknown")

        # Manual / historical overrides BEFORE geocode calls
        norm_key = normalize_place(norm).lower()
        manual_hit = self.manual_fixes.get(norm_key) or self.historical_lookup.get(
            norm_key
        )
        if manual_hit:
            logger.debug(f"📌 Manual/Hist hit → '{norm}' → {manual_hit}")
            return LocationOut(
                raw_name=raw_place,
                normalized_name=manual_hit.get("normalized_name", norm),
                latitude=manual_hit.get("lat"),
                longitude=manual_hit.get("lng"),
                confidence_score=1.0,
                status="manual_override",
                source="manual_or_historical",
                timestamp=datetime.utcnow().isoformat(),
            )

        # --- 2. Fallback coordinates from classifier ----
        if fallback and fallback.get("lat") and fallback.get("lng"):
            logger.debug(f"🗺️ Fallback coords for '{raw_place}': {fallback}")
            return LocationOut(
                raw_name=raw_place,
                normalized_name=norm,
                latitude=fallback["lat"],
                longitude=fallback["lng"],
                confidence_score=normalize_confidence_score(processed.get("confidence")),
                status=status,
                source="fallback",
                timestamp=datetime.utcnow().isoformat(),
            )

        # --- 3. External geocode ------------------------
        geo = self.geocoder.get_or_create_location(None, norm)
        if geo and geo.get("latitude") and geo.get("longitude"):
            logger.debug(f"✅ Geocode OK for '{raw_place}' → {geo}")
            return LocationOut(
                raw_name=raw_place,
                normalized_name=geo.get("normalized_name", norm),
                latitude=geo["latitude"],
                longitude=geo["longitude"],
                confidence_score=float(geo.get("confidence_score", 0.0)),
                status=geo.get("status", "ok"),
                source=geo.get("source", "unknown"),
                timestamp=datetime.utcnow().isoformat(),
            )

        # --- 4. Couldn’t resolve → log and dump ----------
        logger.warning(f"⚠️ UNRESOLVED place '{raw_place}' | Status: {status}")
        self._dump_unresolved(
            {
                "raw_name": raw_place,
                "normalized_name": norm,
                "source_tag": source_tag,
                "event_year": event_year,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        if geo:
            log_unresolved_location(
                {
                    "raw_name": raw_place,
                    "normalized_name": norm,
                    "status": geo.get("status", "unknown"),
                    "source_tag": source_tag,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        return LocationOut(
            raw_name=raw_place,
            normalized_name=norm,
            latitude=None,
            longitude=None,
            confidence_score=0.0,
            status="unresolved",
            source="none",
            timestamp=datetime.utcnow().isoformat(),
        )
