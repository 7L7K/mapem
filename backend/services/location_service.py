"""
LocationService  – central “place resolver” for MaPeM.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from backend.models.location_models import LocationOut
from backend.services.geocode import Geocode
from backend.services.location_processor import process_location


from backend.utils.logger import get_file_logger

logger = get_file_logger("loc_services")

# ...rest of your imports and code...

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────



# ─────────────────────────────────────────────────────────────────────────────
# LocationService
# ─────────────────────────────────────────────────────────────────────────────
class LocationService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_file: Optional[str] = None,
        use_cache: bool = True,
    ):
        self.geocoder = Geocode(api_key=api_key, cache_file=cache_file, use_cache=use_cache)

    # ─────────────────────────────────────────────────────────────────────────
    # Main entry point
    # ─────────────────────────────────────────────────────────────────────────

            
            
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

        result = process_location(
            raw_place,
            source_tag=source_tag,
            event_year=event_year,
            tree_id=tree_id,
            geocoder=self.geocoder,
        )
        return result
logger.debug(
    "✅ LocationService loaded with resolve_location=%s",
    hasattr(LocationService, "resolve_location"),
)
