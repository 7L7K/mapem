#/Users/kingal/mapem/backend/routes/events.py
from flask import Blueprint, jsonify, request
import logging
from uuid import UUID

from flask_cors import cross_origin
from backend.db import get_db
from backend.models import Event, TreeVersion
from backend.utils.debug_routes import debug_route

event_routes = Blueprint("events", __name__, url_prefix="/api/events")
 

@event_routes.route("/", methods=["GET"], strict_slashes=False)
@cross_origin()
@debug_route
def get_events():
    db = next(get_db())
    logger.debug(f"➡️ GET /api/events | args={dict(request.args)}")
    try:
        version_id = request.args.get("version_id", type=int)

        uploaded_id_raw = request.args.get("uploaded_tree_id")
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

        q = db.query(Event)
        if version_id:
            q = q.filter(Event.tree_id == version_id)
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
