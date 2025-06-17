"""
LocationService – central “place resolver” for MapEm.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Any, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.location_models import LocationOut
from backend.models.location import Location
from backend.services.geocode import Geocode
from backend.services.location_processor import process_location
from backend.utils.helpers import normalize_location
from backend.utils.logger import get_file_logger
from backend.config import DATA_DIR

logger = get_file_logger("loc_services")

# tolerance for float comparisons (~1 meter)
EPSILON = 1e-5


class LocationResolutionError(Exception):
    """Raised when a location cannot be resolved or persisted."""
    pass


class LocationService:
    # standardized status/source values
    STATUS_EMPTY = "empty"
    STATUS_UNRESOLVED = "unresolved"
    SOURCE_NONE = "none"

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_file: Optional[str] = None,
        use_cache: bool = True,
        data_dir: Optional[Path] = None,
        mock_mode: bool | None = None,
    ):
        # Set up base data dir (guaranteed Path object)
        self.data_dir = Path(data_dir or Path(DATA_DIR))
        self.data_dir.mkdir(exist_ok=True, parents=True)
        logger.debug("🔍 LocationService using data_dir=%s", self.data_dir)

        # Set up geocoder instance
        self.geocoder = Geocode(
            api_key=api_key,
            cache_file=cache_file,
            use_cache=use_cache,
            mock_mode=mock_mode,
        )

        # Paths for manual fixes, historical lookups, and unresolved logs
        self.manual_fixes_path = self.data_dir / "manual_place_fixes.json"
        self.historical_dir = self.data_dir / "historical_places"
        self.unresolved_path = self.data_dir / "unresolved_locations.json"

        # preload manual fixes & historical data (no-op if files missing)
        self.manual_fixes = self._load_json(self.manual_fixes_path, {})
        self.historical_lookup = self._load_historical_dir(self.historical_dir)

    # ──────────────────────────────────────────────
    # JSON/historical loaders
    # ──────────────────────────────────────────────

    def _load_json(self, path: Path, default: Any) -> Any:
        """Load JSON from path or return default."""
        try:
            import json
            if path.exists():
                return json.loads(path.read_text())
        except Exception:
            logger.warning("⚠️ Failed to load JSON from %s", path)
        return default

    def _load_historical_dir(self, hist_dir: Path) -> dict[str, Any]:
        """Load all JSON files from historical_dir into a lookup dict."""
        data: dict[str, Any] = {}
        for file in hist_dir.glob("*.json"):
            try:
                import json
                data[file.stem] = json.loads(file.read_text())
            except Exception:
                logger.warning("⚠️ Failed to load historical file %s", file)
        return data

    # ──────────────────────────────────────────────
    # Helper methods
    # ──────────────────────────────────────────────

    def _validate_inputs(
        self,
        raw_place: Optional[str],
        event_year: Optional[int],
        source_tag: str,
    ) -> None:
        """Ensure types of inputs are correct."""
        if raw_place is not None and not isinstance(raw_place, str):
            raise TypeError("raw_place must be a string or None")
        if event_year is not None and not isinstance(event_year, int):
            raise TypeError("event_year must be int or None")
        if not isinstance(source_tag, str):
            raise TypeError("source_tag must be a string")

    def _empty_output(self) -> LocationOut:
        """Return a LocationOut representing an empty/unresolved place."""
        return LocationOut(
            raw_name="",
            normalized_name="",
            latitude=None,
            longitude=None,
            confidence_score=0.0,
            status=self.STATUS_EMPTY,
            source=self.SOURCE_NONE,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _normalize_input(self, raw_place: str) -> str:
        """Normalize the raw_place string for lookup."""
        return normalize_location(raw_place) or ""

    def _lookup_existing(
        self,
        session: Session,
        normalized: str,
        lat: float | None = None,
        lng: float | None = None,
    ) -> Location | None:
        """
        Check for an existing Location by normalized name or by
        close-enough latitude/longitude.
        """
        if not normalized:
            return None

        if loc := session.query(Location).filter_by(normalized_name=normalized).first():
            return loc

        if lat is not None and lng is not None:
            return (
                session.query(Location)
                .filter(
                    func.abs(Location.latitude - lat) < EPSILON,
                    func.abs(Location.longitude - lng) < EPSILON,
                )
                .first()
            )
        return None

    def _resolve(
        self,
        raw_place: str,
        event_year: Optional[int],
        source_tag: str,
        tree_id: Optional[str],
    ) -> LocationOut:
        """Delegate to the existing process_location logic."""
        return process_location(
            raw_place,
            source_tag=source_tag,
            event_year=event_year,
            tree_id=tree_id,
            geocoder=self.geocoder,
        )

    def _insert_location(
        self,
        session: Session,
        loc_out: LocationOut,
    ) -> LocationOut:
        """
        Insert a new Location into the DB, or reuse duplicate.
        Rolls back on errors and wraps exceptions.
        """
        try:
            if duplicate := self._lookup_existing(
                session, loc_out.normalized_name, loc_out.latitude, loc_out.longitude
            ):
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
            # context-managed transaction
            with session.begin():
                session.add(loc)

            logger.info("📝 Location inserted '%s' (id=%s)", loc.normalized_name, loc.id)
            return LocationOut.model_validate(loc)

        except Exception as exc:
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
        """Resolve raw_place → LocationOut, optionally persisting to DB."""
        self._validate_inputs(raw_place, event_year, source_tag)

        if not raw_place or not raw_place.strip():
            logger.warning("⛔ resolve_location called with empty input")
            if save and db_session is not None:
                raise LocationResolutionError("raw_place is empty")
            return self._empty_output()

        normalized = self._normalize_input(raw_place)
        logger.info(
            "🌍 Resolving: raw='%s' | norm='%s' | tag=%s | year=%s | tree=%s",
            raw_place, normalized, source_tag, event_year, tree_id,
        )

        if db_session is not None:
            existing = self._lookup_existing(db_session, normalized)
            if existing:
                logger.debug("🔎 Found existing location '%s'", normalized)
                return LocationOut.model_validate(existing)

        loc_out = self._resolve(raw_place, event_year, source_tag, tree_id)

        if save and db_session is not None:
            if loc_out.status == self.STATUS_UNRESOLVED or not loc_out.normalized_name:
                logger.error("❌ Resolution failed for '%s'", raw_place)
                raise LocationResolutionError(f"Location unresolved: {raw_place}")
            loc_out = self._insert_location(db_session, loc_out)

        logger.debug("✅ resolve_location → %s", loc_out)
        return loc_out

    def resolve_many(
        self,
        raw_places: List[str],
        *,
        event_year: Optional[int] = None,
        source_tag: str = "",
        tree_id: Optional[str] = None,
        db_session: Session | None = None,
        save: bool = False,
    ) -> List[LocationOut]:
        """
        Batch-resolve a list of raw_place strings using a single geocoder
        instance and (optional) DB session.
        """
        results: list[LocationOut] = []
        for place in raw_places:
            results.append(
                self.resolve_location(
                    place,
                    event_year=event_year,
                    source_tag=source_tag,
                    tree_id=tree_id,
                    db_session=db_session,
                    save=save,
                )
            )
        return results


logger.debug(
    "✅ LocationService loaded with resolve_location=%s",
    hasattr(LocationService, "resolve_location"),
)
