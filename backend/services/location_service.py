"""
LocationService  – central “place resolver” for MaPeM.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from backend.models.location_models import LocationOut
from backend.services.geocode import Geocode
from backend.services.location_processor import process_location
from backend.utils.logger import get_file_logger
from backend.config import DATA_DIR

logger = get_file_logger("loc_services")


class LocationService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_file: Optional[str] = None,
        use_cache: bool = True,
        data_dir: Optional[Path] = None,
    ):
        # Set up base data dir (guaranteed Path object)
        self.data_dir = Path(
            data_dir
            or Path(DATA_DIR)
        )
        self.data_dir.mkdir(exist_ok=True, parents=True)
        logger.debug("🔍 LocationService using data_dir=%s", self.data_dir)

        # Set up geocoder instance
        self.geocoder = Geocode(
            api_key=api_key, cache_file=cache_file, use_cache=use_cache
        )

        # Manual fix and history support (future expansion)
        self.manual_fixes_path = self.data_dir / "manual_place_fixes.json"
        self.historical_dir = self.data_dir / "historical_places"
        self.unresolved_path = self.data_dir / "unresolved_locations.json"

        # For deep-dive debugging, you can load these below (not in use by default)
        # self.manual_fixes = self._load_json(self.manual_fixes_path, {})
        # self.historical_lookup = self._load_historical_dir(self.historical_dir)

    # ──────────────────────────────────────────────
    # Main entry point
    # ──────────────────────────────────────────────

    def resolve_location(
        self,
        raw_place: Optional[str],
        *,
        event_year: Optional[int] = None,
        source_tag: str = "",
        tree_id: Optional[str] = None,
    ) -> LocationOut:
        if not raw_place:
            logger.warning("⛔ resolve_location called with empty input")
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

        logger.info(
            "🌍 Resolving location: raw='%s' | tag=%s | year=%s | tree=%s",
            raw_place,
            source_tag,
            event_year,
            tree_id,
        )
        result = process_location(
            raw_place,
            source_tag=source_tag,
            event_year=event_year,
            tree_id=tree_id,
            geocoder=self.geocoder,
        )
        logger.debug("✅ resolve_location → %s", result)
        return result

logger.debug(
    "✅ LocationService loaded with resolve_location=%s",
    hasattr(LocationService, "resolve_location"),
)
