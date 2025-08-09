#/Users/kingal/mapem/backend/routes/events.py
from flask import Blueprint, jsonify, request
import logging
from uuid import UUID
from backend.utils.logger import get_file_logger

from flask_cors import cross_origin
from backend.db import get_db
from sqlalchemy import text
from backend.models import Event, TreeVersion
from backend.utils.debug_routes import debug_route

event_routes = Blueprint("events", __name__, url_prefix="/api/events")
logger = get_file_logger("events_route")
 

@event_routes.route("/", methods=["GET"], strict_slashes=False)
@cross_origin()
@debug_route
def get_events():
    db = next(get_db())
    logger.debug(f"➡️ GET /api/events | args={dict(request.args)}")
    try:
        # version_id is a UUID in our schema, but we also support numeric strings from older clients
        version_id_raw = request.args.get("version_id")
        version_id = None
        if version_id_raw:
            try:
                version_id = UUID(version_id_raw)
            except ValueError:
                logger.warning(f"⚠️ Invalid version_id: {version_id_raw}")
                return jsonify({"error": "Invalid version_id"}), 400

        uploaded_id_raw = request.args.get("uploaded_tree_id") or request.args.get("tree_id")
        uploaded_id = None
        if uploaded_id_raw:
            try:
                uploaded_id = UUID(uploaded_id_raw)
            except ValueError:
                logger.warning(f"⚠️ Invalid uploaded_tree_id: {uploaded_id_raw}")
                return jsonify({"error": "Invalid uploaded_tree_id"}), 400

        if uploaded_id and not version_id:
            version = (
                db.query(TreeVersion)
                  .filter(TreeVersion.uploaded_tree_id == uploaded_id)
                  .order_by(TreeVersion.version_number.desc())
                  .first()
            )
            version_id = version.id if version else None
            logger.debug(f"🔍 Resolved version_id={version_id} from uploaded_tree_id={uploaded_id}")

        # Respect strict versioning: require version_id
        if not version_id:
            return jsonify({"error": "version_id required"}), 400
        q = db.query(Event).filter(Event.tree_id == version_id)
        logger.debug(f"🔍 Filtering on tree_id={version_id}")
        logger.debug(f"▶️ Filtering {q.count()} events total for version_id={version_id}")

        results = q.order_by(Event.date).all()
        logger.debug(f"✅ Fetched {len(results)} events")

        out = [e.serialize() for e in results]
        return jsonify(out), 200

    except Exception:
        logger.exception("💥 get_events crashed")
        return jsonify({"error": "Internal server error"}), 500

    finally:
        db.close()
