from __future__ import annotations

import logging
import os
from pathlib import Path

from backend.celery_app import celery_app
from backend.db import SessionLocal
from backend.models import TreeVersion, Job
from backend.services.location_service import LocationService
from backend.services.parser import GEDCOMParser
from backend.services.upload_service import cleanup_temp

logger = logging.getLogger("mapem.upload_tasks")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_gedcom_task(self, file_path: str, tree_name: str, uploaded_tree_id: str, job_id: str | None = None):
    """Background GEDCOM processing."""
    logger.info("📂 [Task] Starting parse %s (tree=%s)", file_path, uploaded_tree_id)

    # 1️⃣ Sanity: file must exist
    if not Path(file_path).exists():
        msg = f"Temp file {file_path} not found."
        logger.error("❌ [Task] %s", msg)
        return {"status": "error", "message": msg}

    try:
        with SessionLocal.begin() as session:
            if job_id:
                job = session.get(Job, job_id)
                if job:
                    job.status = "started"
                    job.progress = 5
            loc = LocationService(api_key=os.getenv("GEOCODE_API_KEY") or "DUMMY_KEY")
            parser = GEDCOMParser(file_path, loc)

            parsed = parser.parse_file()
            logger.info(
                "📑 [Task] Parsed %d people, %d events",
                len(parsed["individuals"]),
                len(parsed["events"]),
            )
            if job_id and job:
                job.progress = 40

            version = TreeVersion(
                uploaded_tree_id=uploaded_tree_id,
                version_number=1,
            )
            session.add(version)
            session.flush()

            summary = parser.save_to_db(
                session,
                uploaded_tree_id=uploaded_tree_id,
                tree_version_id=version.id,
            )
            logger.info(
                "✅ [Task] Saved tree %s → version %s", uploaded_tree_id, version.id
            )
            if job_id and job:
                job.status = "success"
                job.progress = 100
                job.result = {"version_id": str(version.id), "summary": summary}
            return {"status": "success", "summary": summary, "version_id": str(version.id)}

    except Exception as exc:
        logger.exception("❌ [Task] Failure processing tree %s", uploaded_tree_id)
        # Preserve original traceback
        try:
            with SessionLocal.begin() as session:
                if job_id:
                    job = session.get(Job, job_id)
                    if job:
                        job.status = "failure"
                        job.error = str(exc)
        except Exception:
            pass
        raise self.retry(exc=exc) from exc

    finally:
        cleanup_temp(file_path)
