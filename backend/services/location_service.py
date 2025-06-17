"""
LocationService  – central “place resolver” for MaPeM.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Any

from sqlalchemy.orm import Session

from backend.models.location_models import LocationOut
from backend.models.location import Location
from backend.services.geocode import Geocode
from backend.services.location_processor import process_location
from backend.utils.helpers import normalize_location
from backend.utils.logger import get_file_logger
from backend.config import DATA_DIR

logger = get_file_logger("loc_services")


class LocationResolutionError(Exception):
    """Raised when a location cannot be resolved or persisted."""

    pass


class LocationService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_file: Optional[str] = None,
        use_cache: bool = True,
        data_dir: Optional[Path] = None,
        mock_mode: bool | None = None,
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
            api_key=api_key,
            cache_file=cache_file,
            use_cache=use_cache,
            mock_mode=mock_mode,
        )

        # Manual fix and history support (future expansion)
        self.manual_fixes_path = self.data_dir / "manual_place_fixes.json"
        self.historical_dir = self.data_dir / "historical_places"
        self.unresolved_path = self.data_dir / "unresolved_locations.json"

        # For deep-dive debugging, you can load these below (not in use by default)
        # self.manual_fixes = self._load_json(self.manual_fixes_path, {})
        # self.historical_lookup = self._load_historical_dir(self.historical_dir)

    # ──────────────────────────────────────────────
    # Helper methods
    # ──────────────────────────────────────────────

    def _validate_inputs(self, raw_place: Optional[str], event_year: Optional[int], source_tag: str) -> None:
        if raw_place is not None and not isinstance(raw_place, str):
            raise TypeError("raw_place must be a string or None")
        if event_year is not None and not isinstance(event_year, int):
            raise TypeError("event_year must be int or None")
        if not isinstance(source_tag, str):
            raise TypeError("source_tag must be a string")

    def _empty_output(self) -> LocationOut:
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

    def _normalize_input(self, raw_place: str) -> str:
        norm = normalize_location(raw_place) or ""
        return norm

    def _lookup_existing(self, session: Session, normalized: str, lat: float | None = None, lng: float | None = None) -> Location | None:
        if not normalized:
            return None
        loc = session.query(Location).filter_by(normalized_name=normalized).first()
        if loc:
            return loc
        if lat is not None and lng is not None:
            return (
                session.query(Location)
                .filter(Location.latitude == lat, Location.longitude == lng)
                .first()
            )
        return None

    def _resolve(self, raw_place: str, event_year: Optional[int], source_tag: str, tree_id: Optional[str]) -> LocationOut:
        return process_location(
            raw_place,
            source_tag=source_tag,
            event_year=event_year,
            tree_id=tree_id,
            geocoder=self.geocoder,
        )

    def _insert_location(self, session: Session, loc_out: LocationOut) -> LocationOut:
        try:
            duplicate = self._lookup_existing(session, loc_out.normalized_name, loc_out.latitude, loc_out.longitude)
            if duplicate:
                logger.info("↩️ Existing location reused '%s'", loc_out.normalized_name)
                return LocationOut.model_validate(duplicate)

            loc = Location(
                raw_name=loc_out.raw_name,
                normalized_name=loc_out.normalized_name,
                latitude=loc_out.latitude,
                longitude=loc_out.longitude,
                confidence_score=loc_out.confidence_score,
                status=loc_out.status,
                source=loc_out.source,
            )
            session.add(loc)
            session.commit()
            logger.info("📝 Location inserted '%s' (%s)", loc.normalized_name, loc.id)
            return LocationOut.model_validate(loc)
        except Exception as exc:
            session.rollback()
            logger.exception("❌ Failed to insert location '%s'", loc_out.normalized_name)
            raise LocationResolutionError(str(exc)) from exc

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
        db_session: Session | None = None,
        save: bool = False,
    ) -> LocationOut:
        """Resolve ``raw_place`` to a ``LocationOut`` object.

        Parameters
        ----------
        raw_place:
            The unprocessed place string to resolve. Must be a non-empty string.
        event_year:
            Optional year used for historical lookups.
        source_tag:
            Source tag from the GEDCOM import (used for logging only).
        tree_id:
            Identifier of the uploaded tree requesting resolution.
        db_session:
            SQLAlchemy session. If provided and ``save`` is ``True`` the
            resolved location will be persisted to the database.
        save:
            When ``True`` store the resolved location in the database.

        Returns
        -------
        LocationOut
            Normalized location data.

        Raises
        ------
        LocationResolutionError
            If the location cannot be resolved or inserted when ``save``
            is requested.
        """
        self._validate_inputs(raw_place, event_year, source_tag)

        if not raw_place or not raw_place.strip():
            logger.warning("⛔ resolve_location called with empty input")
            if save and db_session is not None:
                raise LocationResolutionError("raw_place is empty")
            return self._empty_output()

        normalized = self._normalize_input(raw_place)
        logger.info(
            "🌍 Resolving location: raw='%s' | norm='%s' | tag=%s | year=%s | tree=%s",
            raw_place,
            normalized,
            source_tag,
            event_year,
            tree_id,
        )

        if db_session is not None:
            existing = self._lookup_existing(db_session, normalized)
            if existing:
                logger.debug("🔎 Found existing location '%s'", normalized)
                out = LocationOut.model_validate(existing)
                return out

        loc_out = self._resolve(raw_place, event_year, source_tag, tree_id)

        if save and db_session is not None:
            if loc_out.status == "unresolved" or not loc_out.normalized_name:
                logger.error("❌ Resolution failed for '%s'", raw_place)
                raise LocationResolutionError(f"Location unresolved: {raw_place}")
            loc_out = self._insert_location(db_session, loc_out)

        logger.debug("✅ resolve_location → %s", loc_out)
        return loc_out

logger.debug(
    "✅ LocationService loaded with resolve_location=%s",
    hasattr(LocationService, "resolve_location"),
)
