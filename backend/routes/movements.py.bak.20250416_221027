# backend/routes/movements.py

from flask import Blueprint, jsonify, current_app
from flask_cors import cross_origin
from sqlalchemy.orm import Session
from backend.models import Event, Individual, Location
from backend.db import SessionLocal

movements_bp = Blueprint("movements", __name__, url_prefix="/api/movements")

@movements_bp.route("/<int:tree_id>", methods=["GET", "OPTIONS"])
@cross_origin(origins="*")
def get_movements(tree_id):
    session: Session = SessionLocal()
    try:
        # Query events directly by tree_id now that it's indexed
        query = (
            session.query(Event, Individual, Location)
            .join(Individual, Event.individual_id == Individual.id)
            .join(Location, Event.location_id == Location.id)
            .filter(Event.tree_id == tree_id)
            # .filter(Event.category == "migration")  # optional: re-enable later
            .filter(Location.latitude.isnot(None), Location.longitude.isnot(None))
            .order_by(Individual.id, Event.date)
        )

        results = query.all()
        if not results:
            current_app.logger.info("No movement data found for tree %s", tree_id)
            return jsonify([]), 200

        grouped = {}
        for event, person, loc in results:
            pid = person.id
            if pid not in grouped:
                grouped[pid] = {
                    "person_id": pid,
                    "person_name": person.name,
                    "movements": []
                }
            grouped[pid]["movements"].append({
                "event_type": event.event_type,
                "year": event.date.year if event.date else None,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "location": loc.name,
                "notes": event.notes
            })

        for data in grouped.values():
            data["movements"].sort(key=lambda m: m["year"] or 0)

        return jsonify(list(grouped.values())), 200

    except Exception as e:
        current_app.logger.exception("❌ Failed to fetch movements for tree %s", tree_id)
        return jsonify(error=str(e)), 500

    finally:
        session.close()
