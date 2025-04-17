# backend/routes/timeline.py

from flask import Blueprint, request, jsonify
from backend.models import Event
from backend.utils.helpers import get_db_connection
from flask_cors import cross_origin

timeline_routes = Blueprint("timeline", __name__, url_prefix="/api/timeline")

@timeline_routes.route("/<int:tree_id>", methods=["GET", "OPTIONS"], strict_slashes=False)
@cross_origin(origins="*")
def get_timeline(tree_id):
    session = get_db_connection()
    try:
        events = (
            session.query(Event)
            .filter(Event.tree_id == tree_id)
            .order_by(Event.date)
            .all()
        )
        timeline = []
        for evt in events:
            if evt.date:
                year = evt.date.year
                label = evt.event_type.title()
                if evt.individual and evt.individual.name:
                    label += f" – {evt.individual.name}"
                timeline.append({"year": str(year), "event": label})

        return jsonify(timeline)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
