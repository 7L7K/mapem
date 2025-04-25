# backend/routes/movements.py

from flask import Blueprint, jsonify, current_app, request
from sqlalchemy.orm import Session
import logging

from backend.db import get_db
from backend.models import Event, Individual, Location

movements_bp = Blueprint("movements", __name__, url_prefix="/api/movements")
logger = logging.getLogger("mapem")

# ────────────────────────────────────────────────────────────────
# 🗺️  Return grouped migration events for a tree
# ────────────────────────────────────────────────────────────────
@movements_bp.route("/<int:tree_id>", methods=["GET"], strict_slashes=False)
def get_movements(tree_id: int):
    """
    Returns a list like:
    [
        {
            "person_id": 12,
            "person_name": "John Doe",
            "movements": [
                {
                    "event_type": "Residence",
                    "year": 1910,
                    "latitude": 33.512,
                    "longitude": -90.252,
                    "location": "Sunflower County, MS",
                    "notes": "Census 1910"
                },
                ...
            ]
        },
        ...
    ]
    """
    db: Session = next(get_db())

    try:
        # Optional filter support (?event_type=Residence) for future use
        event_type = request.args.get("event_type")

        query = (
            db.query(Event, Individual, Location)
            .join(Individual, Event.individual_id == Individual.id)
            .join(Location, Event.location_id == Location.id)
            .filter(Event.tree_id == tree_id)
            .filter(Location.latitude.isnot(None), Location.longitude.isnot(None))
        )

        if event_type:
            query = query.filter(Event.event_type == event_type)

        results = query.order_by(Individual.id, Event.date).all()

        if not results:
            logger.info("No movement data found for tree %s", tree_id)
            return jsonify([]), 200

        # Group events by person
        grouped = {}
        for event, person, loc in results:
            pid = person.id
            grouped.setdefault(
                pid,
                {
                    "person_id": pid,
                    "person_name": person.name,
                    "movements": [],
                },
            )
            grouped[pid]["movements"].append(
                {
                    "event_type": event.event_type,
                    "year": event.date.year if event.date else None,
                    "latitude": loc.latitude,
                    "longitude": loc.longitude,
                    "location": loc.name,
                    "notes": event.notes,
                }
            )

        # Ensure chronological order
        for data in grouped.values():
            data["movements"].sort(key=lambda m: m["year"] or 0)

        return jsonify(list(grouped.values())), 200

    except Exception as e:
        logger.exception("❌ Failed to fetch movements for tree %s", tree_id)
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()
