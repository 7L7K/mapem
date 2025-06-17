import logging
import os
from pathlib import Path

from backend.celery_app import celery_app
from backend.db import SessionLocal
from backend.models import TreeVersion, UploadedTree
from backend.services.location_service import LocationService
from backend.services.parser import GEDCOMParser

logger = logging.getLogger("mapem.upload_tasks")

@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_gedcom_task(self, file_path: str, tree_name: str, uploaded_tree_id: str):
    """Background GEDCOM processing."""
    logger.info("📂 [Task] Starting parse for %s", file_path)
    with SessionLocal.begin() as session:
        try:
            loc = LocationService(api_key=os.getenv("GEOCODE_API_KEY") or "DUMMY_KEY")
            parser = GEDCOMParser(file_path, loc)
            parsed = parser.parse_file()
            logger.info("📑 [Task] Parsed %d individuals, %d events", len(parsed["individuals"]), len(parsed["events"]))

            version = TreeVersion(uploaded_tree_id=uploaded_tree_id, version_number=1)
            session.add(version)
            session.flush()
            summary = parser.save_to_db(session, uploaded_tree_id=uploaded_tree_id, tree_version_id=version.id)
            logger.info("✅ [Task] Saved tree %s version %s", uploaded_tree_id, version.id)
        except Exception as exc:
            logger.exception("❌ [Task] Failed processing tree %s: %s", uploaded_tree_id, exc)
            raise self.retry(exc=exc)
        finally:
            if os.path.exists(file_path):
                try:
                    Path(file_path).unlink()
                except OSError:
                    logger.warning("⚠️ Could not remove temp file %s", file_path)
    return summary
