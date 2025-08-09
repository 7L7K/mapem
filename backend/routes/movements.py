from __future__ import annotations
import logging
from collections import defaultdict
from datetime import date
from math import radians, sin, cos, asin, sqrt
from typing import List, Dict, Any, Tuple

from flask import Blueprint, request, jsonify, abort
from sqlalchemy.orm import joinedload

from backend.db import SessionLocal
from backend.models import UploadedTree, TreeVersion, Event, Individual
from uuid import UUID
from backend.services.query_builders import build_event_query
from backend.services.filters import from_query_args, normalize_filters
from backend.utils.logger import get_file_logger
from backend.utils.redaction import should_redact_person, redact_name, is_authorized

logger = get_file_logger("movements")
movements_routes = Blueprint("movements", __name__, url_prefix="/api/movements")

@movements_routes.route("/<uploaded_tree_id>", methods=["GET"])
def get_movements(uploaded_tree_id: str):
    db = SessionLocal()
    try:
        # 1) Validate tree + version
        try:
            uploaded_uuid = UUID(uploaded_tree_id)
        except ValueError:
            abort(400, description="Invalid uploaded_tree_id")

        tree = db.get(UploadedTree, uploaded_uuid)
        if not tree:
            abort(404, description="UploadedTree not found")

        version = (
            db.query(TreeVersion)
            .filter(TreeVersion.uploaded_tree_id == uploaded_uuid)
            .order_by(TreeVersion.version_number.desc())
            .first()
        )
        if not version:
            abort(404, description="No TreeVersion exists for this tree")

        # 2) Extract & normalize filters from query params (supports yearRange, checkbox maps, etc.)
        raw_filters = from_query_args(request.args)
        filters = normalize_filters(raw_filters)

        # 3) Build & run the filtered events query
        events_q = (
            build_event_query(db, version.id, filters)
            .options(joinedload(Event.participants), joinedload(Event.location))
        )
        events: List[Event] = events_q.all()
        logger.debug("✅ Retrieved %s events after filters", len(events))

        # Determine mode: flat events or segments
        mode = request.args.get("mode", "flat").lower()

        # Lightweight auth: allow full details only for admins
        authorized = is_authorized(request.headers)

        if mode == "flat":
            # Build flat list of event pins
            flat: List[Dict[str, Any]] = []
            for e in events:
                loc = e.location
                if not loc or loc.latitude is None or loc.longitude is None:
                    continue
                for p in e.participants:
                    p: Individual
                    hide = (not authorized) and should_redact_person(p.birth_date, p.death_date)
                    display_name = redact_name(p.full_name) if hide else p.full_name
                    flat.append({
                        "event_id":  e.id,
                        "person_id": str(p.id),
                        "event_type": e.event_type,
                        "date":      str(e.date) if e.date else None,
                        "names":     [display_name],
                        "location":  loc.normalized_name or loc.raw_name,
                        "latitude":  float(loc.latitude),
                        "longitude": float(loc.longitude),
                        "redacted":  hide,
                        "location_id": str(loc.id),
                        "confidence_score": float(getattr(loc, "confidence_score", 0.0) or 0.0),
                        "confidence_label": getattr(loc, "source", ""),
                    })
            logger.debug("📍 Built %s flat events", len(flat))
            return jsonify(flat), 200

        elif mode == "segments":
            # Build movement segments (from-to)
            by_person: Dict[int, List[Event]] = defaultdict(list)
            for e in events:
                for p in e.participants:
                    by_person[p.id].append(e)
            # Sort each person's events by date
            for pid, ev_list in by_person.items():
                ev_list.sort(key=lambda e: e.date or date.min)

            def haversine_km(a: Tuple[float,float], b: Tuple[float,float]) -> float:
                # returns kilometers between two (lat, lng)
                lat1, lon1 = a
                lat2, lon2 = b
                R = 6371.0
                dlat = radians(lat2 - lat1)
                dlon = radians(lon2 - lon1)
                aa = sin(dlat/2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2) ** 2
                c = 2 * asin(sqrt(aa))
                return R * c

            segments: List[Dict[str, Any]] = []
            for pid, ev_list in by_person.items():
                if len(ev_list) < 2:
                    continue
                # Name from first event's participant entry for this person
                person_obj = next((pp for pp in ev_list[0].participants if pp.id == pid), None)
                person_name = person_obj.full_name if person_obj else ""
                hide = (not authorized) and person_obj and should_redact_person(person_obj.birth_date, person_obj.death_date)
                display_name = redact_name(person_name) if hide else person_name
                for prev_evt, curr_evt in zip(ev_list, ev_list[1:]):
                    loc_prev = prev_evt.location
                    loc_curr = curr_evt.location
                    if not loc_prev or not loc_curr:
                        continue
                    if loc_prev.id == loc_curr.id:
                        continue
                    # compute distance & speed if we have both dates
                    distance_km = None
                    speed_km_per_year = None
                    try:
                        if None not in (loc_prev.latitude, loc_prev.longitude, loc_curr.latitude, loc_curr.longitude):
                            distance_km = haversine_km((float(loc_prev.latitude), float(loc_prev.longitude)),
                                                       (float(loc_curr.latitude), float(loc_curr.longitude)))
                        if prev_evt.date and curr_evt.date and distance_km is not None:
                            delta_years = max(0.0001, (curr_evt.date - prev_evt.date).days / 365.25)
                            speed_km_per_year = distance_km / delta_years
                    except Exception:
                        distance_km = None
                        speed_km_per_year = None
                    prev_conf = float(getattr(loc_prev, "confidence_score", 0.0) or 0.0)
                    curr_conf = float(getattr(loc_curr, "confidence_score", 0.0) or 0.0)
                    conf = min(prev_conf, curr_conf)
                    suspicious = (isinstance(speed_km_per_year, (int, float)) and speed_km_per_year >= 2000)
                    impossible = (isinstance(speed_km_per_year, (int, float)) and speed_km_per_year >= 100000)
                    segments.append({
                        "person_ids":   [str(pid)],
                        "names":        [display_name] if display_name else [],
                        "from": {
                            "lat":  loc_prev.latitude,
                            "lng":  loc_prev.longitude,
                            "date": str(prev_evt.date) if prev_evt.date else None,
                            "location_id": str(loc_prev.id),
                            "confidence_score": prev_conf,
                        },
                        "to": {
                            "lat":  loc_curr.latitude,
                            "lng":  loc_curr.longitude,
                            "date": str(curr_evt.date) if curr_evt.date else None,
                            "location_id": str(loc_curr.id),
                            "confidence_score": curr_conf,
                        },
                        "event_type": curr_evt.event_type,
                        "distance_km": distance_km,
                        "speed_km_per_year": speed_km_per_year,
                        "redacted": hide,
                        "confidence_score": conf,
                        "suspicious": suspicious,
                        "impossible": impossible,
                    })
            logger.debug("🧩 Built %s movement segments", len(segments))
            return jsonify(segments), 200

        else:
            abort(400, description=f"Unknown mode '{mode}', use flat or segments")

    except Exception as exc:
        # Pass through 404s from abort, map others to 500
        if hasattr(exc, "code") and getattr(exc, "code", None) == 404:
            return jsonify({"error": str(exc)}), 404
        logger.exception("❌ Failed to fetch movements – %s", exc)
        return jsonify({"error": str(exc)}), 500

    finally:
        db.close()
