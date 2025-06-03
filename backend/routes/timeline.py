# backend/routes/timeline.py
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models import Event
from backend.utils.logger import get_logger
from backend.utils.debug_routes import debug_route

timeline_routes = Blueprint("timeline", __name__, url_prefix="/api/timeline")
logger = get_logger(__name__)

@timeline_routes.route("/<int:tree_id>", methods=["GET"], strict_slashes=False)
@debug_route
def get_timeline(tree_id: int):
    """
    Returns an ordered list of year → label pairs for a given tree.
    Optional ?event_type=<type> filter.
    """
    db: Session = next(get_db())
    try:
        event_type = request.args.get("event_type")

        query = (
            db.query(Event)
            .filter(Event.tree_id == tree_id)
            .order_by(Event.date)
        )
        if event_type:
            query = query.filter(Event.event_type == event_type)

        timeline = []
        for evt in query:
            if not evt.date:
                continue
            label = evt.event_type.title()
            if evt.individual and evt.individual.name:
                label += f" – {evt.individual.name}"
            timeline.append(
                {"year": str(evt.date.year), "event": label}
            )

        return jsonify(timeline), 200

    except Exception as e:
        logger.exception("🔥 timeline failed for tree %s", tree_id)
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()
