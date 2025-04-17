# backend/services/location_service.py
import os
import json
import logging
from datetime import datetime
from typing import Optional


from backend.services.location_processor import process_location, log_unresolved_location
from backend.services.geocode import Geocode
from backend.utils.location_utils import normalize_place
from backend.models.location_models import LocationOut
from backend.utils.helpers import normalize_confidence_score


logger = logging.getLogger(__name__)

class LocationService:
    def __init__(self, api_key=None, cache_file='geocode_cache.json', use_cache=True):
        self.geocoder = Geocode(api_key=api_key, cache_file=cache_file, use_cache=use_cache)
        
        # Load manual overrides and normalize keys.
        manual_fixes_path = os.path.join(os.path.dirname(__file__), "..", "data", "manual_place_fixes.json")
        if os.path.exists(manual_fixes_path):
            with open(manual_fixes_path, "r") as f:
                try:
                    fixes = json.load(f)
                except Exception:
                    fixes = {}
        else:
            fixes = {}
        self.manual_fixes = { normalize_place(k).lower(): v for k, v in fixes.items() }
        
        # Load historical mappings from data/historical_places directory.
        self.historical_lookup = {}
        historical_dir = os.path.join(os.path.dirname(__file__), "..", "data", "historical_places")
        if os.path.exists(historical_dir):
            for fname in os.listdir(historical_dir):
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(historical_dir, fname), "r") as f:
                            data = json.load(f)
                            for k, v in data.items():
                                norm_key = normalize_place(k).lower()
                                self.historical_lookup[norm_key] = v
                    except Exception as e:
                        logger.warning(f"Could not load historical mapping {fname}: {e}")
        logger.info(f"Loaded {len(self.historical_lookup)} historical records.")

    def resolve_location(self, raw_place: Optional[str], event_year=None, source_tag="") -> LocationOut:
        """
        Process a raw place. We'll return a valid LocationOut model even if no lat/lon found.
        """
        if not raw_place:
            # Return an empty LocationOut
            return LocationOut(
                raw_name="",
                normalized_name="",
                latitude=None,
                longitude=None,
                confidence_score=0.0,
                status="empty",
                source="none",
                timestamp=datetime.utcnow().isoformat()
            )

        # Step 1: process_location for classification/fallback
        processed = process_location(raw_place, source_tag=source_tag, event_year=event_year)
        if not processed:
            # fallback if process_location returns None for some reason
            processed = {
                "normalized": "",
                "status": "unknown",
                "note": "No classification",
                "confidence": 0.0,
                "fallback": None
            }

        norm = processed.get("normalized") or ""
        # Step 2: if fallback, short-circuit...
        fb = processed.get("fallback")
        if fb:
            lat = fb.get("lat", None)
            lng = fb.get("lng", None)
            conf = normalize_confidence_score(processed.get("confidence"))

            return LocationOut(
                raw_name=raw_place,
                normalized_name=norm,
                latitude=lat,
                longitude=lng,
                confidence_score=conf,
                status=processed.get("status", "vague"),
                source="fallback",
                timestamp=datetime.utcnow().isoformat()
            )

        # Step 3: external geocode
        geo = self.geocoder.get_or_create_location(None, norm)
        if not geo or geo.get("latitude") is None or geo.get("longitude") is None:
            # log_unresolved_location if needed
            if geo:
                log_unresolved_location({
                    "raw_name": raw_place,
                    "normalized_name": norm,
                    "status": geo.get("status", "unknown"),
                    "source_tag": source_tag,
                    "timestamp": datetime.utcnow().isoformat()
                })

            return LocationOut(
                raw_name=raw_place,
                normalized_name=norm,
                latitude=None,
                longitude=None,
                confidence_score=0.0,
                status=(geo.get("status") if geo else "manual_fix_pending"),
                source=(geo.get("source") if geo else "none"),
                timestamp=datetime.utcnow().isoformat()
            )

        # Step 4: success
        return LocationOut(
            raw_name=raw_place,
            normalized_name=geo.get("normalized_name", norm),
            latitude=geo.get("latitude"),
            longitude=geo.get("longitude"),
            confidence_score=float(geo.get("confidence_score", 0.0)),
            status=geo.get("status", "ok"),
            source=geo.get("source", "unknown"),
            timestamp=datetime.utcnow().isoformat()
        )
