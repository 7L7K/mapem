from __future__ import annotations

"""Movement route – returns geo‑ready events for an uploaded tree."""

import logging
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any

from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload

from backend.db import get_db
from backend.models import Event
from backend.services.filters import (
    normalize_filters,
    explain_filters,
    from_query_args,
)
from backend.services.query_builders import build_event_query
from backend.utils.tree_helpers import get_latest_tree_version
from backend.utils.debug_routes import debug_route
from backend.utils.uuid_utils import parse_uuid_arg_or_400

movements_routes = Blueprint("movements", __name__, url_prefix="/api/movements")
logger = logging.getLogger("mapem.movements")

# ───────────────
# Configs
# ───────────────
US_CENTROID = (37.8, -96.0)  # fallback lat/lng for missing/vague locations
VAGUE_THRESHOLD = 0.6        # everything below this is "vague"


def get_confidence_label(score):
    if score is None:
        return "vague"
    return "precise" if score >= VAGUE_THRESHOLD else "vague"

@movements_routes.route("/<string:uploaded_tree_id>", methods=["GET"])
@debug_route
def get_movements(uploaded_tree_id: str):
    logger.debug("🔥 MOVEMENT ROUTE ACTIVE – uploaded_tree_id=%s", uploaded_tree_id)
    db = next(get_db())

    try:
        # ── Parse Tree UUID ───────────────────────────
        parsed_id = parse_uuid_arg_or_400("uploaded_tree_id", uploaded_tree_id)
        if isinstance(parsed_id, tuple):  # means it failed validation
            return jsonify({"error": "Tree not found"}), 404

        # ── TreeVersion Lookup ────────────────────────
        try:
            version = get_latest_tree_version(db, parsed_id)
        except ValueError:
            logger.warning("🛑 No TreeVersion found for UploadedTree ID: %s", uploaded_tree_id)
            return jsonify({"error": "Tree not found"}), 404

        if version is None:
            logger.warning("🛑 TreeVersion is None for %s", uploaded_tree_id)
            return jsonify({"error": "Tree not found"}), 404

        logger.debug("🧬 TreeVersion resolved → %s", version.id)

        # ── Grouped Flag Handling ─────────────────────
        grouped_flag = str(request.args.get("grouped", "false")).lower() == "true"
        logger.debug("📦 Grouped format requested? %s", grouped_flag)

        # ── Filter Parsing ────────────────────────────
        raw_query = request.args.to_dict(flat=False)
        raw_query.pop("grouped", None)
        raw_filters = from_query_args(raw_query)
        filters = normalize_filters(raw_filters)
        logger.debug("🧪 Parsed filters: %s", filters)

        filter_hint = explain_filters(filters)
        if filter_hint:
            logger.debug("🧪 Filter explanation: %s", filter_hint)

        # ── Run Filtered Query ────────────────────────
        q = build_event_query(db, version.id, filters).options(
            joinedload(Event.participants),
            joinedload(Event.location),
        )

        events: List[Event] = q.all()
        logger.info("✅ Retrieved %s events after filtering", len(events))

        flat: List[Dict[str, Any]] = []
        missing_location = 0
        fallback_used_total = 0

        is_vague_mode = bool(filters.get("vague"))
        for e in events:
            loc = e.location
            participants = list(e.participants)

            # Determine confidence
            confidence_score = getattr(loc, "confidence_score", None) if loc else None
            confidence_label = get_confidence_label(confidence_score)

            # Should we include this event?
            if is_vague_mode:
                if confidence_label != "vague":
                    continue
                # If loc missing OR no lat/lng, use fallback coords
                if not loc or (loc.latitude is None or loc.longitude is None):
                    latitude, longitude = US_CENTROID
                    fallback_used = True
                    fallback_used_total += 1
                else:
                    latitude, longitude = loc.latitude, loc.longitude
                    fallback_used = False
            else:
                # precise mode: only include events with good coords
                if not loc or (loc.latitude is None or loc.longitude is None):
                    missing_location += 1
                    continue
                latitude, longitude = loc.latitude, loc.longitude
                fallback_used = False
                # Skip if confidence is vague in precise mode
                if confidence_label == "vague":
                    continue

            person_ids = [p.id for p in participants]
            names = [p.full_name for p in participants]

            flat.append(
                {
                    "event_id": e.id,
                    "person_ids": person_ids,
                    "person_id": person_ids[0] if len(person_ids) == 1 else None,
                    "event_type": e.event_type,
                    "date": e.date.isoformat() if e.date else None,
                    "latitude": latitude,
                    "longitude": longitude,
                    "confidence_score": confidence_score,
                    "confidence_label": confidence_label,
                    "location": loc.normalized_name if loc else None,
                    "names": names,
                    "notes": e.notes,
                    "filter_explanation": filter_hint,
                    "fallback_used": fallback_used,
                }
            )

        logger.info(
            "🧩 Movement summary → returned=%s | missing_loc=%s | fallback_used=%s",
            len(flat), missing_location, fallback_used_total
        )

        if not flat:
            logger.warning("⚠️ No events returned after filtering")

        # ── Grouped Format Handling ─────────────────────
        if grouped_flag:
            grouped: Dict[Any, Dict[str, Any]] = defaultdict(lambda: {
                "person_ids": [],
                "names": [],
                "movements": [],
                "person_id": None,
            })
            for row in flat:
                key = tuple(sorted(row["person_ids"])) or ("unknown",)
                grp = grouped[key]
                grp["person_ids"] = row["person_ids"]
                grp["person_id"] = row["person_id"]
                grp["names"] = row["names"]
                grp["movements"].append(
                    {
                        "event_type": row["event_type"],
                        "year": int(row["date"][:4]) if row["date"] else None,
                        "latitude": row["latitude"],
                        "longitude": row["longitude"],
                        "confidence_label": row["confidence_label"],
                        "location": row["location"],
                        "notes": row["notes"],
                    }
                )
            for entry in grouped.values():
                entry["movements"].sort(key=lambda m: m["year"] or 0)
            return jsonify(list(grouped.values())), 200

        return jsonify(flat), 200

    except Exception as exc:
        logger.exception("❌ Failed to fetch movements – %s", exc)
        return jsonify({"error": "Server error fetching movements"}), 500

    finally:
        db.close()
