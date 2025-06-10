# backend/routes/geocode_api.py

import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from backend.services.location_processor import process_location
from backend.utils.logger import get_file_logger

logger = get_file_logger("geocode_route")

# path for unresolved‐geocode log
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
UNRESOLVED_GEO_LOG = os.path.join(LOG_DIR, "unresolved_geocodes.jsonl")

bp = Blueprint("geocode_route", __name__, url_prefix="/api")


@bp.route("/geocode")
def geocode_place():
    place = request.args.get("place", "").strip()
    logger.debug("➡️ Received /api/geocode?place=%r", place)

    if not place:
        logger.warning("❌ Missing 'place' parameter in request")
        return jsonify({"error": "missing 'place' param"}), 400

    db = current_app.session_maker()
    try:
        loc = process_location(place, db_session=db)

        # 1) Null return → unresolved
        if loc is None:
            logger.warning("🟠 Location unresolved: %r", place)
            entry = {
                "raw_name": place,
                "timestamp": datetime.utcnow().isoformat(),
                "reason": "null_return"
            }
            with open(UNRESOLVED_GEO_LOG, "a") as f:
                f.write(json.dumps(entry) + "\n")
            return jsonify({"status": "unresolved"}), 200

        # 2) Missing coords → unresolved
        if loc.latitude is None or loc.longitude is None:
            logger.warning("🟠 Location missing lat/lng: %r", place)
            entry = {
                "raw_name": place,
                "timestamp": datetime.utcnow().isoformat(),
                "reason": "no_latlng"
            }
            with open(UNRESOLVED_GEO_LOG, "a") as f:
                f.write(json.dumps(entry) + "\n")
            return jsonify({"status": "unresolved"}), 200

        # 3) Success
        logger.info("✅ Geocode success: %r → (%.6f, %.6f)",
                    place, loc.latitude, loc.longitude)

        return jsonify({
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "normalized": loc.normalized_name,
            "status": loc.status,
            "timestamp": loc.timestamp or datetime.utcnow().isoformat(),
        }), 200

    except Exception as e:
        logger.exception("💥 Error while geocoding place: %r", place)
        return (
            jsonify({"error": "internal error", "details": str(e)}),
            500,
            {"Content-Type": "application/json"},
        )
    finally:
        db.close()
