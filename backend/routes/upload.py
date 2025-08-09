from __future__ import annotations

import os
import subprocess
import sys
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Final, Tuple

from celery.result import AsyncResult
from flask import Blueprint, jsonify, request

from backend.db import SessionLocal
from backend.models import TreeVersion, UploadedTree, Job
from backend.services.location_service import LocationService
from backend.services.parser import GEDCOMParser
from backend.services.upload_service import (
    MAX_FILE_SIZE_MB,
    validate_upload,
    save_file,
    cleanup_temp,
)
from backend.utils.helpers import increment_upload_count
from backend.utils.debug_routes import debug_route
from backend.utils.logger import get_file_logger

logger = get_file_logger("upload")

# ─────────────────────────────
# Config
# ─────────────────────────────
upload_routes: Final = Blueprint("upload", __name__, url_prefix="/api/upload")

ASYNC_THRESHOLD_MB: Final[int] = int(
    os.getenv("UPLOAD_ASYNC_THRESHOLD_MB", "10")
)  # env-tunable

GEDCOM_FILE_KEYS: Final[Tuple[str, ...]] = ("gedcom_file", "gedcom", "file")

# ─────────────────────────────
# Helpers
# ─────────────────────────────
@debug_route
def _build_location_service() -> LocationService:
    api_key = (
        os.getenv("GEOCODE_API_KEY")
        or os.getenv("GOOGLE_MAPS_API_KEY")
        or "DUMMY_KEY"
    )
    return LocationService(api_key=api_key)


def _next_version_number(db, uploaded_tree_id: int) -> int:
    last = (
        db.query(TreeVersion.version_number)
        .filter(TreeVersion.uploaded_tree_id == uploaded_tree_id)
        .order_by(TreeVersion.version_number.desc())
        .first()
    )
    return (last[0] + 1) if last else 1


def _extract_file():
    for key in GEDCOM_FILE_KEYS:
        if key in request.files:
            return request.files[key], key
    return None, None


def _check_duplicate_tree(db, tree_name: str) -> bool:
    """Return True if a tree with this name already exists."""
    return db.query(UploadedTree).filter_by(tree_name=tree_name).first() is not None


# ─────────────────────────────
# Status endpoint (frontend polls)
# ─────────────────────────────
@upload_routes.route("/status/<task_id>", methods=["GET"], strict_slashes=False)
@debug_route
def upload_status(task_id: str):
    res = AsyncResult(task_id)
    return (
        jsonify({"state": res.state, "info": res.info}),
        200,
    )


# ─────────────────────────────
# Main upload route
# ─────────────────────────────
@upload_routes.route("/", methods=["POST"], strict_slashes=False)
@debug_route
def upload_tree():
    """Handle GEDCOM upload → parse → commit to DB.  
    Large files route to Celery for async processing.
    """
    request_id = uuid.uuid4().hex[:8]  # tie logs together
    temp_path: str | None = None
    async_queued = False

    logger.info("📥 [%s] Upload route hit", request_id)
    logger.debug("[%s] Headers: %s", request_id, dict(request.headers))
    logger.debug("[%s] Form keys: %s", request_id, list(request.form.keys()))
    logger.debug("[%s] File keys: %s", request_id, list(request.files.keys()))

    try:
        # 1️⃣ Locate and validate the file
        file, matched_key = _extract_file()
        ok, message, size_mb = validate_upload(file)
        if not ok:
            return jsonify({"error": message}), 400

        logger.debug("[%s] Using file field '%s': %s", request_id, matched_key, file.filename)
        logger.info(
            "➡️ [%s] file received (%s) — %.2f MB",
            request_id,
            file.filename,
            size_mb,
        )

        # 2️⃣ Validate tree name (required)
        tree_name = request.form.get("tree_name")
        if not tree_name:
            return jsonify({"error": "Missing tree_name"}), 400

        # Optional simulate-only flag (no DB writes)
        simulate = (request.form.get("simulate", "false").lower() == "true")

        # 3️⃣ Fail-fast duplicate check **before** touching disk or Celery
        with SessionLocal.begin() as db:
            if not simulate and _check_duplicate_tree(db, tree_name):
                return jsonify({"error": "Tree name already exists"}), 400

        # 4️⃣ Save GEDCOM to temp file
        temp_path = save_file(file)
        logger.info("[%s] Temp GEDCOM saved → %s", request_id, temp_path)

        # 5️⃣ Large files get queued to Celery
        if not simulate and size_mb > ASYNC_THRESHOLD_MB:
            with SessionLocal.begin() as db:
                uploaded_tree = UploadedTree(tree_name=tree_name)
                db.add(uploaded_tree)
                db.flush()
                job = Job(
                    task_id="",
                    job_type="gedcom_import",
                    status="queued",
                    progress=0,
                    params={"tree_name": tree_name, "uploaded_tree_id": str(uploaded_tree.id)},
                )
                db.add(job)
                db.flush()

            from backend.tasks.upload_tasks import process_gedcom_task

            task = process_gedcom_task.delay(
                temp_path, tree_name, str(uploaded_tree.id), str(job.id)
            )
            # store Celery task id
            with SessionLocal.begin() as db:
                j = db.get(Job, job.id)
                if j:
                    j.task_id = task.id
            async_queued = True
            logger.info(
                "📤 [%s] GEDCOM queued async (task=%s, tree=%s)",
                request_id,
                task.id,
                uploaded_tree.id,
            )
            return (
                jsonify(
                    status="queued",
                    uploaded_tree_id=str(uploaded_tree.id),
                    task_id=task.id,
                    job_id=str(job.id),
                ),
                202,
            )

        # 6️⃣ Parse GEDCOM synchronously
        location_service = _build_location_service()
        parser = GEDCOMParser(temp_path, location_service)
        logger.info("🧬 [%s] Parsing GEDCOM for tree %s", request_id, tree_name)
        parsed = parser.parse_file()
        logger.info(
            "✅ [%s] Parsed %d individuals, %d events",
            request_id,
            len(parsed["individuals"]),
            len(parsed["events"]),
        )

        # In simulate mode, return dry-run summary with warnings (no DB writes)
        if simulate:
            summary = {
                "people_count": len(parsed.get("individuals", [])),
                "event_count": len(parsed.get("events", [])),
                "warnings": [
                    "Simulate-only: no DB writes",
                    "Dates/places validated best-effort",
                ],
                "errors": [],
            }
            return (
                jsonify(
                    status="simulated",
                    uploaded_tree_id=None,
                    version_id=None,
                    summary=summary,
                    tree_id=None,
                    version=None,
                ),
                200,
            )

        with SessionLocal.begin() as db:
            # Insert UploadedTree + TreeVersion
            uploaded_tree = UploadedTree(tree_name=tree_name)
            db.add(uploaded_tree)
            db.flush()

            version = TreeVersion(
                uploaded_tree_id=uploaded_tree.id,
                version_number=_next_version_number(db, uploaded_tree.id),
            )
            db.add(version)
            db.flush()

            # Save parsed data
            summary = parser.save_to_db(
                session=db,
                uploaded_tree_id=uploaded_tree.id,
                tree_version_id=version.id,
                dry_run=False,
            )
            logger.info(
                "🧾 [%s] Upload summary: %s people, %s events",
                request_id,
                summary.get("people_count", "NA"),
                summary.get("event_count", "NA"),
            )

            # Update upload counter + trigger retry script every 5 uploads
            count = increment_upload_count()
            logger.debug("[%s] upload_count=%s", request_id, count)
            if count % 5 == 0:
                script = (
                    Path(__file__).resolve().parents[2] / "scripts" / "retry_unresolved.py"
                )
                logger.info("[%s] Running unresolved retry batch", request_id)
                try:
                    subprocess.run([sys.executable, str(script)], check=True)
                except Exception as exc:
                    logger.warning("[%s] retry_unresolved.py failed: %s", request_id, exc)

            return (
                jsonify(
                    status="success",
                    uploaded_tree_id=str(uploaded_tree.id),
                    version_id=str(version.id),
                    summary=summary,
                    tree_id=str(uploaded_tree.id),
                    version=version.version_number,
                ),
                200,
            )

    except Exception as exc:
        logger.error("‼ [%s] upload_tree failed: %s", request_id, exc)
        logger.error(traceback.format_exc())
        return (
            jsonify(
                error="Upload failed",
                details=str(exc),
                trace=traceback.format_exc(),
            ),
            500,
        )

    finally:
        # Clean up temp file when handled synchronously
        if temp_path and not async_queued:
            cleanup_temp(temp_path)
