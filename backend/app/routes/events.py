from flask import Blueprint, request, jsonify
from app.models import Event
from backend.app.db import get_db_connection
from datetime import datetime

event_routes = Blueprint("events", __name__, url_prefix="/api/events")

@event_routes.route("/", methods=["GET"])
def get_events():
    tree_id = request.args.get("tree_id")
    category = request.args.get("category")
    person_id = request.args.get("person_id")
    start_year = request.args.get("start_year")
    end_year = request.args.get("end_year")

    session = get_db_connection()
    try:
        query = session.query(Event)
        if tree_id:
            query = query.filter(Event.tree_id == int(tree_id))
        if category:
            query = query.filter(Event.category == category)
        if person_id:
            query = query.filter(Event.individual_id == int(person_id))
        if start_year:
            query = query.filter(Event.date >= datetime(int(start_year), 1, 1))
        if end_year:
            query = query.filter(Event.date <= datetime(int(end_year), 12, 31))

        events = query.all()
        results = []
        for evt in events:
            event_dict = {
                "id": evt.id,
                "event_type": evt.event_type,
                "date": evt.date.isoformat() if evt.date else None,
                "date_precision": evt.date_precision,
                "notes": evt.notes,
                "source_tag": evt.source_tag,
                "category": evt.category,
            }
            if evt.individual:
                event_dict["individual"] = {"id": evt.individual.id, "name": evt.individual.name}
            if evt.location:
                event_dict["location"] = {
                    "name": evt.location.name,
                    "normalized_name": evt.location.normalized_name,
                    "latitude": evt.location.latitude,
                    "longitude": evt.location.longitude,
                    "confidence": evt.location.confidence_score
                }
            results.append(event_dict)
        return jsonify(results)
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500
    finally:
        session.close()
