"""
Trees API routes (clean v2)

Endpoints
---------
GET  /api/trees/                         → latest version of every uploaded tree
GET  /api/trees/<tree_id>/counts         → simple counts (individual / family)
GET  /api/trees/<tree_id>/visible-counts → counts after UI filters
POST /api/trees/<tree_id>/visible-counts → same but JSON body
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from backend.db import get_db
from backend.models import TreeVersion, UploadedTree, Event, Individual, Family
from backend.utils.tree_helpers import get_latest_tree_version
from backend.services.filters import normalize_filters, from_query_args
from backend.services.query_builders import build_event_query
from backend.utils.debug_routes import debug_route
from backend.models.event import event_participants   # ⬅️ NEW
from backend.utils.uuid_utils import parse_uuid_arg_or_400

log = logging.getLogger("mapem")

tree_routes = Blueprint("trees", __name__, url_prefix="/api/trees")

# ─── validation helpers ─────────────────────────────────────────────────────
_ALLOWED_KEYS = {
    "eventTypes", "yearRange", "year", "vague",
    "confidenceThreshold", "sources", "person", "relations",
}
_VALID_EVENT_TYPES = {"birth", "death", "marriage", "divorce", "residence"}

def _validate_filter_keys(f: Dict[str, Any]) -> None:
    bad = set(f) - _ALLOWED_KEYS
    if bad:
        raise ValueError(f"Unexpected filter keys: {', '.join(sorted(bad))}")

def _validate_filter_types(f: Dict[str, Any]) -> None:
    if "eventTypes" in f:
        if not isinstance(f["eventTypes"], dict):
            raise ValueError("eventTypes must be a dict[str,bool]")
        for k, v in f["eventTypes"].items():
            if not isinstance(k, str) or not isinstance(v, bool):
                raise ValueError("eventTypes must map str→bool")
            if k.lower() not in _VALID_EVENT_TYPES:
                raise ValueError(f"Invalid eventType: {k}")
    if "yearRange" in f:
        yr = f["yearRange"]
        ok = (
            isinstance(yr, list)
            and len(yr) == 2
            and all((y is None or isinstance(y, int)) for y in yr)
        )
        if not ok:
            raise ValueError("yearRange must be [int|None, int|None]")
    if "sources" in f or "relations" in f:
        for key in ("sources", "relations"):
            if key in f:
                val = f[key]
                if not isinstance(val, dict) or not all(
                    isinstance(k, str) and isinstance(v, bool) for k, v in val.items()
                ):
                    raise ValueError(f"{key} must map str→bool")
    if "vague" in f and not isinstance(f["vague"], bool):
        raise ValueError("vague must be boolean")
    if "confidenceThreshold" in f and not isinstance(f["confidenceThreshold"], (int, float)):
        raise ValueError("confidenceThreshold must be numeric")


# ─── GET /api/trees/ ────────────────────────────────────────────────────────
@tree_routes.route("/", methods=["GET"])
@debug_route
def list_trees():
    db = next(get_db())
    subq = (
        db.query(
            TreeVersion.uploaded_tree_id,
            func.max(TreeVersion.version_number).label("max_version"),
        )
        .group_by(TreeVersion.uploaded_tree_id)
        .subquery()
    )

    rows = (
        db.query(TreeVersion, UploadedTree.tree_name)
        .join(
            subq,
            (TreeVersion.uploaded_tree_id == subq.c.uploaded_tree_id)
            & (TreeVersion.version_number == subq.c.max_version),
        )
        .join(UploadedTree, TreeVersion.uploaded_tree_id == UploadedTree.id)
        .all()
    )

    payload = [
        {
            "tree_id":          tv.id,
            "uploaded_tree_id": tv.uploaded_tree_id,
            "tree_name":        name,
            "version_number":   tv.version_number,
            "created_at":       tv.created_at.isoformat(),
        }
        for tv, name in rows
    ]
    return jsonify({"trees": payload}), 200


# ─── GET /api/trees/<tree_id>/counts ────────────────────────────────────────
@tree_routes.route("/<string:tree_id>/counts", methods=["GET"])
@debug_route
def basic_counts(tree_id: str):
    # parse & require a valid TreeVersion.id
    parsed = parse_uuid_arg_or_400("tree_id", tree_id)
    if isinstance(parsed, tuple):
        return parsed

    db = next(get_db())
    tv = db.query(TreeVersion).filter_by(id=parsed).first()
    if not tv:
        return jsonify({"error": "TreeVersion not found"}), 404

    people_count   = (
        db.query(Individual)
          .filter(Individual.tree_id == tv.id)
          .count()
    )
    families_count = (
        db.query(Family)
        .filter(Family.tree_id == tv.id)
        .count()
    )
    event_counts = dict(
        db.query(Event.event_type, func.count(Event.id))
        .filter(Event.tree_id == tv.id)
        .group_by(Event.event_type)
        .all()
    )

    return jsonify({
        "individuals": people_count,
        "families":    families_count,
        "events":      event_counts,
    }), 200

# ─── GET /api/trees/<uploaded_tree_id>/counts (fallback for frontend) ───────
@tree_routes.route("/<string:uploaded_tree_id>/uploaded-counts", methods=["GET"])
@debug_route
def uploaded_tree_counts(uploaded_tree_id: str):
    """Support frontend calls using uploaded_tree_id instead of version_id."""
    db = next(get_db())
    parsed = parse_uuid_arg_or_400("uploaded_tree_id", uploaded_tree_id)
    if isinstance(parsed, tuple):
        return parsed

    # Try resolving the latest TreeVersion for this uploaded_tree
    uploaded = db.query(UploadedTree).filter_by(id=parsed).first()
    if not uploaded:
        return jsonify({"error": "UploadedTree not found"}), 404

    latest = (
    db.query(TreeVersion)
    .filter(TreeVersion.uploaded_tree_id == uploaded.id)
    .order_by(TreeVersion.version_number.desc())
    .first()
)

    if not latest:
        return jsonify({"error": "No TreeVersion found"}), 404

    # Use same logic as `basic_counts()` but inline
    people_count   = (
        db.query(Individual)
          .filter(Individual.tree_id == latest.id)
          .count()
    )
    families_count = (
        db.query(Family)
        .filter(Family.tree_id == latest.id)
        .count()
    )
    event_counts = dict(
        db.query(Event.event_type, func.count(Event.id))
        .filter(Event.tree_id == latest.id)
        .group_by(Event.event_type)
        .all()
    )

    return jsonify({
        "individuals": people_count,
        "families":    families_count,
        "events":      event_counts,
    }), 200


# ─── GET / POST /api/trees/<uploaded_tree_id>/visible-counts ───────────────
@tree_routes.route("/<string:uploaded_tree_id>/visible-counts",
                   methods=["GET", "POST"])
@debug_route
def visible_counts(uploaded_tree_id: str):
    parsed = parse_uuid_arg_or_400("uploaded_tree_id", uploaded_tree_id)
    if isinstance(parsed, tuple):
        return parsed

    db = next(get_db())

    # ─── load raw filters ──────────────────────────────────────────────
    if request.method == "POST":
        raw = request.get_json(silent=True) or {}
    else:
        raw = from_query_args(request.args)

    # also support ?filters= JSON blob
    if "filters" in request.args:
        try:
            raw = json.loads(request.args["filters"])
        except Exception:
            return jsonify({"error": "Bad filters JSON"}), 400

    # force yearRange from repeated query params
    yr = request.args.getlist("yearRange", type=int)
    if yr:
        raw["yearRange"] = yr

    # ─── upfront validation of keys & types ──────────────────────────────
    # validate unknown keys always; only enforce types on POST (JSON body)
    try:
        _validate_filter_keys(raw)
        _validate_filter_types(raw)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # ─── resolve tree version ────────────────────────────────────────────
    try:
        version = get_latest_tree_version(db, parsed)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    # ─── normalize & coerce filters ──────────────────────────────────────
    try:
        filters = normalize_filters(raw)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    # ─── build & execute counts queries ──────────────────────────────────
    try:
        event_q = build_event_query(db, version.id, filters)

        event_counts = dict(
            event_q
            .with_entities(Event.event_type, func.count(Event.id))
            .group_by(Event.event_type)
            .all()
        )

        indiv_count = (
            event_q
            .join(event_participants, Event.id == event_participants.c.event_id)
            .with_entities(event_participants.c.individual_id)
            .distinct()
            .count()
        )

        # (families not yet supported)
        fam_count = 0

        return jsonify({
            "events":   event_counts,
            "people":   indiv_count,
            "families": fam_count,
        }), 200

    except Exception:
        log.exception("❌ Counting failed")
        return jsonify({"error": "Internal server error"}), 500

    finally:
        db.close()
