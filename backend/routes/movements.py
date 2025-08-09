from __future__ import annotations
import logging
from collections import defaultdict
from datetime import date
from typing import List, Dict, Any

from flask import Blueprint, request, jsonify, abort
from sqlalchemy.orm import joinedload

from backend.db import SessionLocal
from backend.models import UploadedTree, TreeVersion, Event
from uuid import UUID
from backend.services.query_builders import build_event_query
from backend.utils.logger import get_file_logger

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

        # 2) Extract filters from query params
        filters = {
            "eventTypes": request.args.get("eventTypes"),
            "year": {
                "min": request.args.get("yearMin", type=int),
                "max": request.args.get("yearMax", type=int),
            },
            "vague": request.args.get("vague", "false").lower() == "true",
            "person": request.args.get("person"),
            "relations": request.args.get("relations"),
            "sources": request.args.get("sources"),
        }

        # 3) Build & run the filtered events query
        events_q = (
            build_event_query(db, version.id, filters)
            .options(joinedload(Event.participants), joinedload(Event.location))
        )
        events: List[Event] = events_q.all()
        logger.debug("✅ Retrieved %s events after filters", len(events))

        # Determine mode: flat events or segments
        mode = request.args.get("mode", "flat").lower()

        if mode == "flat":
            # Build flat list of event pins
            flat: List[Dict[str, Any]] = []
            for e in events:
                loc = e.location
                if not loc or loc.latitude is None or loc.longitude is None:
                    continue
                for p in e.participants:
                    flat.append({
                        "event_id":  e.id,
                        "person_id": p.id,
                        "event_type": e.event_type,
                        "date":      str(e.date) if e.date else None,
                        "names":     [p.full_name],
                        "location":  loc.normalized_name or loc.raw_name,
                        "latitude":  float(loc.latitude),
                        "longitude": float(loc.longitude),
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

            segments: List[Dict[str, Any]] = []
            for pid, ev_list in by_person.items():
                if len(ev_list) < 2:
                    continue
                names = [p.full_name for p in ev_list[0].participants] if ev_list[0].participants else []
                for prev_evt, curr_evt in zip(ev_list, ev_list[1:]):
                    loc_prev = prev_evt.location
                    loc_curr = curr_evt.location
                    if not loc_prev or not loc_curr:
                        continue
                    if loc_prev.id == loc_curr.id:
                        continue
                    segments.append({
                        "person_ids":   [pid],
                        "names":        names,
                        "from": {
                            "lat":  loc_prev.latitude,
                            "lng":  loc_prev.longitude,
                            "date": str(prev_evt.date) if prev_evt.date else None,
                        },
                        "to": {
                            "lat":  loc_curr.latitude,
                            "lng":  loc_curr.longitude,
                            "date": str(curr_evt.date) if curr_evt.date else None,
                        },
                        "event_type": curr_evt.event_type,
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
