# backend/routes/geocode_api.py

import os
import csv
import io
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, after_this_request, Response, send_file
from sqlalchemy import text  # <--- PATCH: Import text!
from backend.services.location_processor import process_location
from backend.utils.logger import get_file_logger
from backend.config import LOG_DIR

logger = get_file_logger("geocode_route")
os.makedirs(LOG_DIR, exist_ok=True)

bp = Blueprint("geocode_route", __name__, url_prefix="/api/admin/geocode")
UNRESOLVED_GEO_LOG = LOG_DIR / "unresolved_geocodes.jsonl"

# -- helper -------------------------------------------------------------
def _close_session(db):
    @after_this_request
    def teardown(resp):
        db.close()
        return resp

# ---------- SUMMARY METRICS ----------
@bp.route("/stats")
def geocode_stats():
    db = current_app.session_maker()
    _close_session(db)

    try:
        total      = db.execute(text("SELECT COUNT(*) FROM locations")).scalar() or 0
        resolved   = db.execute(text("SELECT COUNT(*) FROM locations WHERE status='ok'")).scalar() or 0
        unresolved = db.execute(text("SELECT COUNT(*) FROM locations WHERE status='unresolved'")).scalar() or 0
        manual     = db.execute(text("SELECT COUNT(*) FROM locations WHERE status='manual_override'")).scalar() or 0
        failed = db.execute(
            text("SELECT COUNT(*) FROM locations WHERE status::text = :s"),
            {"s": "failed"}
        ).scalar() or 0


        last_upload = db.execute(text("SELECT MAX(updated_at) FROM locations")).scalar()
        last_manual_fix = db.execute(
    text("SELECT MAX(updated_at) FROM locations WHERE status='manual_override'")
).scalar()

        # Convert datetimes to ISO strings (frontend expects string, not datetime obj)
        last_upload = last_upload.isoformat() if last_upload else None
        last_manual_fix = last_manual_fix.isoformat() if last_manual_fix else None

        # CamelCase all response keys to match FE
        data = {
            "total": total,
            "resolved": resolved,
            "unresolved": unresolved,
            "manual": manual,
            "failed": failed,
            "lastUpload": last_upload,
            "lastManualFix": last_manual_fix,
        }
        return jsonify({"data": data, "error": None})
    except Exception as e:
        logger.error("Error in /stats: %s", e, exc_info=True)
        return jsonify({"data": None, "error": str(e)}), 500

# ---------- UNRESOLVED TABLE ----------
@bp.route("/unresolved")
def geocode_unresolved():
    db = current_app.session_maker()
    _close_session(db)

    try:
        rows = db.execute(text("""
        SELECT 
            l.id,
            l.raw_name,
            l.normalized_name,
            l.confidence_score,
            COUNT(e.id) AS event_count,
            MAX(e.date) AS last_seen
        FROM locations l
        LEFT JOIN events e ON e.location_id = l.id
        WHERE l.status = 'unresolved'
        GROUP BY l.id, l.raw_name, l.normalized_name, l.confidence_score
        ORDER BY last_seen DESC NULLS LAST
    """)).fetchall()


        def serialize_unresolved(r):
            return {
                "id": r.id,
                "rawName": r.raw_name,
                "normalizedName": r.normalized_name,
                "confidence": r.confidence_score,
                "eventCount": r.event_count,
                "lastSeen": r.last_seen.isoformat() if r.last_seen else None,
            }

        data = [serialize_unresolved(r) for r in rows]
        return jsonify({"data": data, "error": None})
    except Exception as e:
        logger.error("Error in /unresolved: %s", e, exc_info=True)
        return jsonify({"data": None, "error": str(e)}), 500

# ---------- HISTORY TABLE ----------
@bp.route("/history")
def geocode_history():
    db = current_app.session_maker()
    _close_session(db)

    try:
        rows = db.execute(text("""
  SELECT
    id,
    raw_name,
    normalized_name,
    latitude,
    longitude,
    updated_at AS fixed_at
  FROM locations
  WHERE status='manual_override'
  ORDER BY updated_at DESC
""")).fetchall()

        data = [dict(r._mapping) for r in rows]
        return jsonify({"data": data, "error": None})
    except Exception as e:
        logger.error("Error in /history: %s", e, exc_info=True)
        return jsonify({"data": None, "error": str(e)}), 500

# ---------- EXPORT (NEW) ----------
@bp.route("/export", methods=["POST"])
def geocode_export():
    """
    Exports location records as CSV filtered by optional treeId & status.
    Body: { treeId: int | null, status: 'unresolved'|'manual'|'all', ... }
    """
    db = current_app.session_maker()
    _close_session(db)

    body = request.get_json(force=True) or {}
    tree_id = body.get("treeId")
    status  = body.get("status", "all")

    try:
        sql = "SELECT id, raw_name, normalized_name, status, confidence_score, lat, lng, last_seen FROM locations"
        params = {}
        where = []

        if status and status != "all":
            where.append("status = :status")
            params["status"] = status if status != "manual" else "manual_override"

        if tree_id:
            where.append("tree_id = :tree_id")
            params["tree_id"] = tree_id

        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY id ASC"

        rows = db.execute(text(sql), params).fetchall()  # <-- PATCH HERE

        # build CSV in-memory
        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(["id", "raw_name", "normalized_name", "status", "confidence", "lat", "lng", "last_seen"])
        for r in rows:
            writer.writerow([
                r.id, r.raw_name, r.normalized_name, r.status,
                r.confidence_score, r.lat, r.lng,
                r.last_seen.isoformat() if r.last_seen else ""
            ])
        csv_bytes = io.BytesIO(si.getvalue().encode("utf-8"))

        filename = f"geocode_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        logger.info("Export %s rows → %s", len(rows), filename)

        return send_file(
            csv_bytes,
            mimetype="text/csv",
            as_attachment=True,
            download_name=filename,
        )

    except Exception as e:
        logger.error("Error in /export: %s", e, exc_info=True)
        return jsonify({"data": None, "error": str(e)}), 500

# ---------- MANUAL FIX ----------
@bp.route("/fix/<int:id>", methods=["POST"])
def geocode_fix(id):
    db = current_app.session_maker()
    _close_session(db)

    body = request.get_json(force=True)
    lat, lng = body.get("lat"), body.get("lng")
    if lat is None or lng is None:
        return jsonify({"data": None, "error": "Missing lat/lng"}), 400

    try:
        db.execute(
            text(
                "UPDATE locations SET lat = :lat, lng = :lng, status = 'manual_override', fixed_at = :now "
                "WHERE id = :id"
            ),
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
    _close_session(db)

    try:
        row = db.execute(
            text("SELECT raw_name FROM locations WHERE id = :id"), {"id": id}
        ).fetchone()
        if not row:
            return jsonify({"data": None, "error": "Not found"}), 404

        process_location(row.raw_name, db_session=db, force_retry=True)
        db.commit()
        return jsonify({"data": {"id": id, "message": "Retry queued"}, "error": None})
    except Exception as e:
        db.rollback()
        logger.error("Error in /retry: %s", e, exc_info=True)
        return jsonify({"data": None, "error": str(e)}), 500

# ---------- PUBLIC SHORTCUT ----------
@bp.route("/../geocode/retry", methods=["POST"])
def public_retry_shortcut():
    """Compat: POST /api/geocode/retry?place_id=... to match spec."""
    place_id = request.args.get("place_id", type=int)
    if not place_id:
        return jsonify({"error": "place_id is required"}), 400
    # Reuse existing handler by delegating
    return geocode_retry(place_id)
