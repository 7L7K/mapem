from __future__ import annotations

"""Movement route – returns geo‑ready events for an uploaded tree.

✓ 404 when the uploaded‑tree ID is valid but no TreeVersion exists
✓ Clean, single‑pass formatting loop (removed earlier duplicate)
✓ Graceful fallbacks for vague locations
✓ Explicit session closing in finally
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any

from flask import Blueprint, request, jsonify, abort
from sqlalchemy.exc import NoResultFound, StatementError
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import NotFound


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
from backend.utils.event_helpers import primary_participant

movements_routes = Blueprint("movements", __name__, url_prefix="/api/movements")
logger = logging.getLogger("mapem.movements")


@movements_routes.route("/<string:uploaded_tree_id>", methods=["GET"])
@debug_route
def get_movements(uploaded_tree_id: str):  # noqa: C901 – complex but readable
    """Return migration events (map markers) for the latest TreeVersion of *uploaded_tree_id*.

    Query‑string filters are parsed by *from_query_args()* and *normalize_filters()*.
    If *grouped=true* is present, the JSON is grouped by participant set.
    """

    logger.debug("🔥 MOVEMENT ROUTE ACTIVE – uploaded_tree_id=%s", uploaded_tree_id)

    # We always close the generator‑based DB session, no matter what happens.
    db = next(get_db())
    try:
        # ── Parse & validate UUID ─────────────────────────────────────────────
        parsed_id = parse_uuid_arg_or_400("uploaded_tree_id", uploaded_tree_id)
        if isinstance(parsed_id, tuple):  # -> (jsonify(), 400)
            return parsed_id

        # ── Resolve latest TreeVersion ────────────────────────────────────────
        try:
            version = get_latest_tree_version(db, parsed_id)
        except ValueError as e:
            logger.warning("🛑 No TreeVersion found for UploadedTree ID: %s", uploaded_tree_id)
            raise NotFound(f"Tree {uploaded_tree_id} not found") from e

        if version is None:
            logger.warning("🛑 get_latest_tree_version() returned None for %s", uploaded_tree_id)
            abort(404, description=f"Tree {uploaded_tree_id} not found")

        logger.debug("🧬 TreeVersion resolved → %s (uploaded_tree=%s)", version.id, uploaded_tree_id)

        # ── Build filters from query args ─────────────────────────────────────
        raw_query: Dict[str, List[str]] = request.args.to_dict(flat=False)
        raw_filters = from_query_args(raw_query)
        filters = normalize_filters(raw_filters)
        logger.debug("🧪 Raw query: %s", raw_query)
        logger.debug("🧪 Normalized filters: %s", filters)

        hint = explain_filters(filters)
        if hint:
            logger.debug("⚠️ Filter explanation: %s", hint)

        # ── Query events ──────────────────────────────────────────────────────
        q = build_event_query(db, version.id, filters).options(
            joinedload(Event.participants),
            joinedload(Event.location),
        )
        events: List[Event] = q.all()
        logger.debug("✅ Retrieved %s events after filters", len(events))

        # ── Transform events → flat list ------------------------------------------------
        flat: List[Dict[str, Any]] = []
        missing_location = 0
        missing_participants = 0
        fallback_used_total = 0

        for e in events:
            loc = getattr(e, "location", None)
            participants = list(e.participants)  # ensure list, even if empty

            # Handle location vagueness / fallback
            if not loc or (loc.latitude is None or loc.longitude is None):
                if filters.get("vague") and loc and loc.normalized_name:
                    lat, lng = 37.8, -96.0  # continental US centroid
                    fallback_used = True
                    fallback_used_total += 1
                    logger.debug("⚠️ Using fallback lat/lng for vague location: %s", loc.normalized_name)
                else:
                    missing_location += 1
                    continue  # skip – can’t plot what we can’t place
            else:
                lat, lng = loc.latitude, loc.longitude
                fallback_used = False

            if not participants:
                missing_participants += 1

            person_ids = [p.id for p in participants]
            names = [p.full_name for p in participants]

            flat.append(
                {
                    "event_id": e.id,
                    "person_ids": person_ids,
                    "event_type": e.event_type,
                    "date": e.date.isoformat() if e.date else None,
                    "lat": lat,
                    "lng": lng,
                    "location": (loc.normalized_name or loc.raw_name) if loc else None,
                    "names": names,
                    "notes": e.notes,
                    "filter_explanation": hint,
                    "fallback_used": fallback_used,
                }
            )

        logger.debug(
            "🧩 Movement summary → returned=%s | missing_location=%s | missing_participants=%s | fallback_used=%s",
            len(flat),
            missing_location,
            missing_participants,
            fallback_used_total,
        )

        if not flat:
            logger.warning("⚠️ No movements passed filtering or geolocation checks")

        # ── Optional grouped format -----------------------------------------------------
        if request.args.get("grouped", "false").lower() == "true":
            grouped: Dict[Any, Dict[str, Any]] = defaultdict(lambda: {
                "person_ids": [],
                "names": [],
                "movements": [],
            })
            for row in flat:
                key = tuple(sorted(row["person_ids"])) or ("unknown",)
                grp = grouped[key]
                grp["person_ids"] = row["person_ids"]
                grp["names"] = row["names"]
                grp["movements"].append(
                    {
                        "event_type": row["event_type"],
                        "year": int(row["date"][:4]) if row["date"] else None,
                        "latitude": row["lat"],
                        "longitude": row["lng"],
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
        return jsonify({"error": str(exc)}), 500

    finally:
        # Make *sure* the session is gone so tests see committed rows.
        db.close()
