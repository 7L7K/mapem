from __future__ import annotations

import logging
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Final

from flask import Blueprint, jsonify, request

import subprocess
import sys
from backend.db import SessionLocal
from backend.models import TreeVersion, UploadedTree
from backend.services.location_service import LocationService
from backend.services.parser import GEDCOMParser
from backend.services.upload_service import validate_upload, save_file
from backend.utils.helpers import increment_upload_count
from backend.utils.debug_routes import debug_route
from backend.utils.logger import get_file_logger

logger = get_file_logger("upload")

# ──────────────────────────────
# Config
# ──────────────────────────────
upload_routes: Final = Blueprint("upload", __name__, url_prefix="/api/upload")

ASYNC_THRESHOLD_MB: Final[int] = 10
GEDCOM_FILE_KEYS: Final[tuple[str, ...]] = ("gedcom_file", "gedcom", "file")

# ──────────────────────────────
# Helpers
# ──────────────────────────────
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

# ──────────────────────────────
# Routes
# ──────────────────────────────
@upload_routes.route("/", methods=["POST"], strict_slashes=False)
@debug_route
def upload_tree():
    """Handle GEDCOM upload → parse → commit to DB using context manager."""
    temp_path: str | None = None
    async_queued = False

    logger.debug("📬 Headers: %s", dict(request.headers))
    logger.debug("📝 Form keys: %s", list(request.form.keys()))
    logger.debug("📎 File keys: %s", list(request.files.keys()))
    logger.info("📥 Upload route hit")

    try:
        # 1️⃣ Locate and validate the file
        file, matched_key = _extract_file()
        ok, message, size_mb = validate_upload(file)
        if not ok:
            return jsonify({"error": message}), 400

        logger.debug("🗂 Using file field '%s': %s", matched_key, getattr(file, "filename", "?"))
        logger.info(
            "➡️ POST /api/upload — file received (%s), size %.2f MB",
            file.filename,
            size_mb,
        )

        # 2️⃣ Validate tree name
        tree_name = request.form.get("tree_name")
        if not tree_name:
            return jsonify({"error": "Missing tree_name"}), 400

        # 3️⃣ Save GEDCOM to temp file
        temp_path = save_file(file)
        logger.debug("💾 Temp GEDCOM saved to %s", temp_path)
        logger.info("📂 GEDCOM saved to %s", temp_path)

        # Large files are processed asynchronously
        if size_mb > ASYNC_THRESHOLD_MB:
            with SessionLocal.begin() as db:
                dup = db.query(UploadedTree).filter_by(tree_name=tree_name).first()
                if dup:
                    return jsonify({"error": "Tree name already exists"}), 400

                uploaded_tree = UploadedTree(tree_name=tree_name)
                db.add(uploaded_tree)
                db.flush()

            from backend.tasks.upload_tasks import process_gedcom_task
            task = process_gedcom_task.delay(temp_path, tree_name, str(uploaded_tree.id))
            logger.info("📤 GEDCOM queued for async processing: task=%s", task.id)
            async_queued = True
            return (
                jsonify(status="queued", uploaded_tree_id=str(uploaded_tree.id), task_id=task.id),
                202,
            )

        # 4️⃣ Parse GEDCOM
        location_service = _build_location_service()
        parser = GEDCOMParser(temp_path, location_service)
        logger.info("🧬 Parsing GEDCOM for tree: %s", tree_name)
        parsed = parser.parse_file()
        logger.info(
            "✅ Parsed %d individuals, %d events",
            len(parsed["individuals"]),
            len(parsed["events"]),
        )

        with SessionLocal.begin() as db:
            try:
                # 5️⃣ Insert UploadedTree + TreeVersion
                dup = db.query(UploadedTree).filter_by(tree_name=tree_name).first()
                if dup:
                    return jsonify({"error": "Tree name already exists"}), 400

                uploaded_tree = UploadedTree(tree_name=tree_name)
                db.add(uploaded_tree)
                db.flush()
                logger.debug("🌳 UploadedTree ID: %s", uploaded_tree.id)

                version = TreeVersion(
                    uploaded_tree_id=uploaded_tree.id,
                    version_number=_next_version_number(db, uploaded_tree.id),
                )
                db.add(version)
                db.flush()
                logger.debug("📚 TreeVersion ID: %s", version.id)

                # 6️⃣ Save parsed data to DB
                logger.debug("💾 Saving to database ...")
                summary = parser.save_to_db(
                    session=db,
                    uploaded_tree_id=uploaded_tree.id,
                    tree_version_id=version.id,
                    dry_run=False,
                )
                logger.info(
                    "🧾 Upload Summary: %s people, %s events",
                    summary.get("people_count", "NA"),
                    summary.get("event_count", "NA"),
                )
                logger.info("🌐 Geocoding completed")
                logger.debug("✅ save_to_db() complete — summary: %s", summary)

                logger.info(
                    "✅ GEDCOM '%s' processed (tree %s, version %s)",
                    file.filename,
                    uploaded_tree.id,
                    version.id,
                )
                logger.info("🎉 Upload and parse complete!")

                count = increment_upload_count()
                logger.debug("📈 upload_count updated to %s", count)
                if count % 5 == 0:
                    script = (
                        Path(__file__).resolve().parents[2]
                        / "scripts"
                        / "retry_unresolved.py"
                    )
                    logger.info("🔁 Running unresolved retry batch — count=%s", count)
                    try:
                        subprocess.run([sys.executable, str(script)], check=True)
                    except Exception as exc:
                        logger.error("⚠️ retry_unresolved.py failed: %s", exc)

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
                logger.error("❌ GEDCOM upload failed: %s", exc)
                logger.error(traceback.format_exc())
                return (
                    jsonify(
                        error="Upload failed",
                        details=str(exc),
                        trace=traceback.format_exc(),
                    ),
                    500,
                )
            # Session closes automatically after with-block

    except Exception as exc:
        logger.error("‼ ERROR in upload_tree: %s", exc)
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
        if temp_path and os.path.exists(temp_path) and not async_queued:
            try:
                os.remove(temp_path)
                logger.debug("🧹 Removed temp file %s", temp_path)
            except OSError as err:
                logger.warning("⚠️ Could not remove temp file %s: %s", temp_path, err)
