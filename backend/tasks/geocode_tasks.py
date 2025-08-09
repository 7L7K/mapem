import logging
import os
from sqlalchemy.orm import sessionmaker

from backend.celery_app import celery_app
from backend.db import get_engine
from backend.models.location import Location
from backend.models import Job
from sqlalchemy import func
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from backend.services.geocode import Geocode
from backend.services.location_service import LocationService

# Set up SQLAlchemy session factory
engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, autocommit=False)

# ⛓️ Load API Key
API_KEY = os.getenv("GEOCODE_API_KEY")
if not API_KEY:
    logging.getLogger(__name__).warning(
        "⚠️ GEOCODE_API_KEY not found in env — geocoder will fallback only."
    )

# 🔧 Geocoder instance
geocoder = Geocode(api_key=API_KEY)

# 📟 Logger for visibility
logger = logging.getLogger("mapem.geocode_tasks")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def geocode_location_task(self, location_id: int, job_id: str | None = None):
    with SessionLocal() as session:
        try:
            loc = session.get(Location, location_id)
            if not loc:
                logger.warning(f"[GeocodeTask] Location id={location_id} not found.")
                return

            if loc.latitude is not None and loc.longitude is not None and loc.geom is not None:
                logger.info(f"[GeocodeTask] id={location_id} already geocoded, skipping.")
                return

            # 🔍 Attempt resolution with era-aware context (no hints available here yet)
            result = geocoder.get_or_create_location(
                session,
                loc.raw_name,
                event_year=None,
                admin_hint=None,
                family_coords=None,
            )
            if result is None:
                raise ValueError(f"Geocoder returned no data for '{loc.raw_name}'")

            # ✅ Apply fields
            loc.latitude         = result.latitude
            loc.longitude        = result.longitude
            loc.normalized_name  = result.normalized_name
            loc.confidence_score = result.confidence_score
            loc.status           = result.status
            loc.source           = result.source
            loc.geocoded_at      = getattr(result, "geocoded_at", None)
            loc.geocoded_by      = getattr(result, "geocoded_by", None)

            # set PostGIS geom
            if result.latitude is not None and result.longitude is not None:
                try:
                    loc.geom = from_shape(Point(result.longitude, result.latitude), srid=4326)
                except Exception:
                    logger.warning("[GeocodeTask] Unable to set geom for id=%s", location_id)
            session.commit()
            if job_id:
                try:
                    job = session.get(Job, job_id)
                    if job:
                        job.status = "success"
                        job.progress = 100
                        job.result = {"location_id": str(loc.id)}
                        session.commit()
                except Exception:
                    session.rollback()
            logger.info(f"[GeocodeTask] ✅ id={location_id} -> ({loc.latitude}, {loc.longitude})")

        except Exception as err:
            session.rollback()
            logger.exception(f"[GeocodeTask] ❌ Error on id={location_id}, retrying…")
            raise self.retry(exc=err)


@celery_app.task(bind=True, max_retries=1, default_retry_delay=5)
def batch_geocode_task(self, places: list[str]):
    """Batch resolve a list of place strings with rate-limited providers.

    - Deduplicates inputs
    - Prefers local Gazetteer before external API
    - Persists new Locations when resolved
    """
    with SessionLocal() as session:
        try:
            svc = LocationService(api_key=API_KEY, use_cache=True)
            unique = []
            seen = set()
            for p in places or []:
                p = (p or "").strip()
                if not p:
                    continue
                if p in seen:
                    continue
                seen.add(p)
                unique.append(p)

            logger.info("[BatchGeocode] queue=%d unique=%d", len(places or []), len(unique))
            saved = 0
            for raw in unique:
                try:
                    out = svc.resolve_location(raw, db_session=session, save=True)
                    if out and out.latitude is not None and out.longitude is not None:
                        saved += 1
                except Exception:
                    logger.exception("[BatchGeocode] failed: '%s'", raw)
            session.commit()
            logger.info("[BatchGeocode] ✅ saved=%d", saved)
        except Exception as err:
            session.rollback()
            logger.exception("[BatchGeocode] ❌ error, retrying…")
            raise self.retry(exc=err)
