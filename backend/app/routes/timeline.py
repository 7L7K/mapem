from flask import Blueprint, jsonify
from app.models import Event
from app.utils.helpers import get_db_connection

timeline_routes = Blueprint("timeline", __name__, url_prefix="/api/timeline")

@timeline_routes.route("/<int:tree_id>", methods=["GET"])
def get_timeline(tree_id):
    session = get_db_connection()
    try:
        events = session.query(Event).filter(Event.tree_id == tree_id).all()
        timeline = []
        for evt in events:
            if evt.date:
                year = evt.date.year
                label = evt.event_type.title()
                if evt.individual:
                    label += f" – {evt.individual.name}"
                timeline.append({"year": str(year), "event": label})
        timeline.sort(key=lambda x: x["year"])
        return jsonify(timeline)
    finally:
        session.close()
