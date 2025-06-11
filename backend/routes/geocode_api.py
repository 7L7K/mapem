# backend/routes/geocode_api.py

import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, after_this_request
from backend.services.location_processor import process_location
from backend.utils.logger import get_file_logger
from backend.config import LOG_DIR

logger = get_file_logger("geocode_route")
os.makedirs(LOG_DIR, exist_ok=True)

bp = Blueprint("geocode_route", __name__, url_prefix="/api/admin/geocode")
UNRESOLVED_GEO_LOG = LOG_DIR / "unresolved_geocodes.jsonl"

# ---------- SUMMARY METRICS ----------
@bp.route("/stats")
def geocode_stats():
    db = current_app.session_maker()
    @after_this_request
    def teardown(resp):
        db.close()
        return resp

    try:
        total      = db.execute("SELECT COUNT(*) FROM locations").scalar()
        resolved   = db.execute("SELECT COUNT(*) FROM locations WHERE status='ok'").scalar()
        unresolved = db.execute("SELECT COUNT(*) FROM locations WHERE status='unresolved'").scalar()
        manual     = db.execute("SELECT COUNT(*) FROM locations WHERE status='manual_override'").scalar()
        failed     = db.execute("SELECT COUNT(*) FROM locations WHERE status='fail'").scalar()
        data = {
            "total": total,
            "resolved": resolved,
            "unresolved": unresolved,
            "manual": manual,
            "failed": failed,
            "last_upload": None,
            "last_manual_fix": None,
        }
        return jsonify({"data": data, "error": None})
    except Exception as e:
        logger.error("Error in /stats: %s", e, exc_info=True)
        return jsonify({"data": None, "error": str(e)}), 500

# ---------- UNRESOLVED TABLE ----------
@bp.route("/unresolved")
def geocode_unresolved():
    db = current_app.session_maker()
    @after_this_request
    def teardown(resp):
        db.close()
        return resp

    try:
        rows = db.execute(
            "SELECT id, raw_name, normalized_name, confidence_score, event_count, last_seen "
            "FROM locations WHERE status='unresolved' ORDER BY last_seen DESC"
        ).fetchall()
        data = [dict(r._mapping) for r in rows]
        return jsonify({"data": data, "error": None})
    except Exception as e:
        logger.error("Error in /unresolved: %s", e, exc_info=True)
        return jsonify({"data": None, "error": str(e)}), 500

# ---------- HISTORY TABLE ----------
@bp.route("/history")
def geocode_history():
    db = current_app.session_maker()
    @after_this_request
    def teardown(resp):
        db.close()
        return resp

    try:
        rows = db.execute(
            "SELECT id, raw_name, normalized_name, lat AS latitude, lng AS longitude, fixed_at "
            "FROM locations WHERE status='manual_override' ORDER BY fixed_at DESC"
        ).fetchall()
        data = [dict(r._mapping) for r in rows]
        return jsonify({"data": data, "error": None})
    except Exception as e:
        logger.error("Error in /history: %s", e, exc_info=True)
        return jsonify({"data": None, "error": str(e)}), 500

# ---------- MANUAL FIX ----------
@bp.route("/fix/<int:id>", methods=["POST"])
def geocode_fix(id):
    db = current_app.session_maker()
    @after_this_request
    def teardown(resp):
        db.close()
        return resp

    body = request.get_json(force=True)
    lat, lng = body.get("lat"), body.get("lng")
    if lat is None or lng is None:
        return jsonify({"data": None, "error": "Missing lat/lng"}), 400

    try:
        db.execute(
            "UPDATE locations SET lat = :lat, lng = :lng, status = 'manual_override', fixed_at = :now "
            "WHERE id = :id",
            {"lat": lat, "lng": lng, "now": datetime.utcnow(), "id": id}
        )
        db.commit()
        return jsonify({"data": {"id": id, "lat": lat, "lng": lng}, "error": None})
    except Exception as e:
        db.rollback()
        logger.error("Error in /fix: %s", e, exc_info=True)
        return jsonify({"data": None, "error": str(e)}), 500

# ---------- RETRY UNRESOLVED ----------
@bp.route("/retry/<int:id>", methods=["POST"])
def geocode_retry(id):
    db = current_app.session_maker()
    @after_this_request
    def teardown(resp):
        db.close()
        return resp

    try:
        row = db.execute(
            "SELECT raw_name FROM locations WHERE id = :id", {"id": id}
        ).fetchone()
        if not row:
            return jsonify({"data": None, "error": "Not found"}), 404

        process_location(row._mapping["raw_name"], db_session=db, force_retry=True)
        db.commit()
        return jsonify({"data": {"id": id, "message": "Retry queued"}, "error": None})
    except Exception as e:
        db.rollback()
        logger.error("Error in /retry: %s", e, exc_info=True)
        return jsonify({"data": None, "error": str(e)}), 500
