from __future__ import annotations

from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import text
from backend.services.location_processor import process_location

geocode_public = Blueprint("geocode_public", __name__, url_prefix="/api/geocode")


@geocode_public.post("/retry")
def retry_public():
    place_id = request.args.get("place_id", type=int)
    if not place_id:
        return jsonify({"error": "place_id is required"}), 400

    db = current_app.session_maker()
    try:
        row = db.execute(text("SELECT raw_name FROM locations WHERE id = :id"), {"id": place_id}).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        process_location(row.raw_name, db_session=db, force_retry=True)
        db.commit()
        return jsonify({"id": place_id, "message": "Retry queued"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()