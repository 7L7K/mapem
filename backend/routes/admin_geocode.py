from datetime import datetime
from flask import Blueprint, jsonify, request, abort
from sqlalchemy import func

from backend.db import SessionLocal
from backend.models import Location, event_participants, Event
from sqlalchemy import text
from backend.services.suggestions import suggest_coordinates as suggest_for_location

admin_geo = Blueprint("admin_geo", __name__, url_prefix="/api/admin/geocode")


def _location_to_dict(loc: Location):
    return {
        "id": loc.id,
        "rawName": loc.raw_name,
        "normalizedName": loc.normalized_name,
        "confidence": loc.confidence_score or 0.0,
        "eventCount": len(loc.events),
        "lastSeen": loc.last_seen.isoformat() if loc.last_seen else None,
    }


@admin_geo.get("/unresolved")
def unresolved_locations():
    with SessionLocal() as session:
        locs = (
            session.query(Location)
            .filter(Location.status.in_(("unresolved", "low_confidence")))
            .order_by(func.coalesce(Location.confidence_score, 0).asc())
            .all()
        )
        return jsonify(data=[_location_to_dict(loc) for loc in locs])


@admin_geo.post("/fix")
def fix_location():
    body = request.get_json(silent=True) or {}
    loc_id = body.get("id")
    lat = body.get("lat")
    lng = body.get("lng")

    if loc_id is None or lat is None or lng is None:
        abort(400, "id, lat, and lng are required")

    with SessionLocal() as session:
        loc: Location = session.get(Location, loc_id)
        if not loc:
            abort(404, f"Location {loc_id} not found")

        # Use correct field names and set PostGIS geom
        loc.latitude  = float(lat)
        loc.longitude = float(lng)
        loc.status    = "manual_override"
        loc.updated_at = datetime.utcnow()
        try:
            session.execute(
                text("UPDATE locations SET geom = ST_SetSRID(ST_Point(:lng,:lat),4326) WHERE id=:id"),
                {"lat": float(lat), "lng": float(lng), "id": loc_id}
            )
        except Exception:
            pass

        print(f"[Fix] {loc_id=} {loc.latitude=} {loc.longitude=} status={loc.status}")
        session.commit()

    return jsonify(success=True)


@admin_geo.get("/suggest")
def suggest_location():
    loc_id = request.args.get("id", type=int)
    if not loc_id:
        abort(400, "Missing location id")

    with SessionLocal() as session:
        loc = session.get(Location, loc_id)
        if not loc:
            abort(404, f"Location {loc_id} not found")

        print(f"\n[SUGGEST] Called for Location {loc.id} ({loc.normalized_name or loc.raw_name})")

        # Run suggest pipeline
        result = suggest_for_location(loc)
        events = (
            session.query(Event)
            .filter(Event.location_id == loc.id)
            .all()
        )
        event_summaries = get_event_summary(events)


        if not result:
            print(f"[SUGGEST] ❌ No suggestion found for {loc.normalized_name or loc.raw_name}")
            return jsonify({
                "suggested": None,
                "events": event_summaries,
                "location": {
                    "id": loc.id,
                    "raw_name": loc.raw_name,
                    "normalized_name": loc.normalized_name,
                },
                "error": "No suggestion found."
            }), 404

        print(f"[SUGGEST] ✅ Suggestion: {result}")

        return jsonify({
            "suggested": result,
            "events": event_summaries,
            "location": {
                "id": loc.id,
                "raw_name": loc.raw_name,
                "normalized_name": loc.normalized_name,
            }
        })


def get_event_summary(events):
    summaries = []
    for e in events:
        summary = {
            "type": e.event_type,
            "year": e.date.year if e.date else None,
            "notes": e.notes or "",
            "person_ids": [p.id for p in e.participants] if e.participants else [],
        }
        summaries.append(summary)
    return summaries
