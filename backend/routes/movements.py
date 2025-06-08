from __future__ import annotations
import logging
from collections import defaultdict
from datetime import datetime, date
from typing import List, Dict, Any

from flask import Blueprint, request, jsonify, abort
from sqlalchemy.orm import joinedload

from backend.db import SessionLocal
from backend.models import (
    UploadedTree,
    TreeVersion,
    Event,
    Family,
    TreeRelationship,
)
from backend.services.query_builders import build_event_query

 
movements_routes = Blueprint("movements", __name__, url_prefix="/api/movements")
from backend.utils.logger import get_file_logger
logger = get_file_logger("movements")

@movements_routes.route("/<uploaded_tree_id>", methods=["GET"])
def get_movements(uploaded_tree_id: str):
    db = SessionLocal()
    

    try:
        # 1) Validate tree + version
        tree = db.query(UploadedTree).get(uploaded_tree_id)
        if not tree:
            abort(404, description="UploadedTree not found")

        version = (
            db.query(TreeVersion)
            .filter(TreeVersion.uploaded_tree_id == uploaded_tree_id)
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
            "personIds": request.args.get("personIds"),
            "familyId": request.args.get("familyId"),
            "relations": request.args.get("relations"),  # could be JSON string
            "sources": request.args.get("sources"),
        }
        group_mode = request.args.get("grouped")

        # 3) Build & run the filtered events query
        events_q = (
            build_event_query(db, version.id, filters)
            .options(joinedload(Event.participants), joinedload(Event.location))
        )
        events: List[Event] = events_q.all()
        logger.debug("✅ Retrieved %s events after filters", len(events))

        # 4) Group events by person and sort by date
        by_person: Dict[int, List[Event]] = defaultdict(list)
        for e in events:
            for p in e.participants:
                by_person[p.id].append(e)

        for pid, ev_list in by_person.items():
            ev_list.sort(key=lambda e: e.date or date.min)


        # 5) Build movement segments
        movements: List[Dict[str, Any]] = []
        for pid, ev_list in by_person.items():
            if len(ev_list) < 2:
                continue  # need at least two events to move

            names = [p.full_name for p in ev_list[0].participants] if ev_list[0].participants else []

            for prev, curr in zip(ev_list, ev_list[1:]):
                loc_prev = prev.location
                loc_curr = curr.location
                if not loc_prev or not loc_curr:
                    continue
                if loc_prev.id == loc_curr.id:
                    continue

                movements.append({
                    "person_ids": [pid],
                    "names": names,
                    "from": {
                        "lat": loc_prev.latitude,
                        "lng": loc_prev.longitude,
                        "date": str(prev.date) if prev.date else None,
                    },
                    "to": {
                        "lat": loc_curr.latitude,
                        "lng": loc_curr.longitude,
                        "date": str(curr.date) if curr.date else None,
                    },
                    "event_type": curr.event_type,
                })

        logger.debug("🧩 Built %s movement segments", len(movements))
        logger.debug("🕓 Event date types: %s", set(type(e.date) for e in ev_list if e.date))

        if group_mode == "person":
            grouped = defaultdict(list)
            for m in movements:
                pid = m["person_ids"][0]
                grouped[pid].append(m)
            return jsonify(grouped), 200

        if group_mode == "family":
            fam_map = {}
            families = db.query(Family).filter(Family.tree_id == version.id).all()
            for fam in families:
                for pid in [fam.husband_id, fam.wife_id]:
                    if pid:
                        fam_map[pid] = fam.id
                child_rows = (
                    db.query(TreeRelationship.related_person_id)
                    .filter(
                        TreeRelationship.tree_id == fam.tree.uploaded_tree_id,
                        TreeRelationship.person_id.in_(
                            filter(None, [fam.husband_id, fam.wife_id])
                        ),
                    )
                    .all()
                )
                for r in child_rows:
                    fam_map[r[0]] = fam.id

            grouped = defaultdict(list)
            for m in movements:
                pid = m["person_ids"][0]
                fid = fam_map.get(pid)
                if fid:
                    grouped[fid].append(m)
            return jsonify(grouped), 200

        return jsonify(movements), 200

    except Exception as exc:
        logger.exception("❌ Failed to fetch movements – %s", exc)
        return jsonify({"error": str(exc)}), 500

    finally:
        db.close()
