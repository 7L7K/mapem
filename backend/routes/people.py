"""
People API endpoints.

Key points
──────────
• Path param <tree_id> is an **UploadedTree ID**.
• We resolve the latest TreeVersion for that upload and work  against
  Individuals whose tree_id == <TreeVersion.id>.
• Extra logging on every step for easy tracing.
"""

from __future__ import annotations

import logging
from typing import Tuple
from uuid import UUID
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from backend.utils.uuid_utils import parse_uuid_arg_or_400
from backend.db import get_db
from backend.models import Individual, TreeVersion, UploadedTree
from backend.utils.debug_routes import debug_route
from backend.utils.uuid_utils import parse_uuid_arg_or_400
from backend.utils.debug_routes import debug_route


people_routes = Blueprint("people", __name__, url_prefix="/api/people")
log = logging.getLogger("mapem")

# ─────────────────────────────────────────────────────────────────────────────
# Helper utilities
# ─────────────────────────────────────────────────────────────────────────────


def _get_latest_version(db, upload_id: UUID) -> Tuple[TreeVersion | None, int]:
    tv = (db.query(TreeVersion)
            .filter_by(uploaded_tree_id=upload_id)
            .order_by(TreeVersion.version_number.desc())
            .first())
    if tv:
        return tv, 200
    exists = db.query(UploadedTree.id).filter_by(id=upload_id).scalar()
    return None, (404 if not exists else 500)


def _validated_pagination() -> Tuple[int, int]:
    """Parse ?limit & ?offset safely with sane defaults."""
    try:
        limit = int(request.args.get("limit", 100))
    except ValueError:
        limit = 100
    try:
        offset = int(request.args.get("offset", 0))
    except ValueError:
        offset = 0
    return max(1, min(limit, 500)), max(0, offset)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/people/<uploaded_tree_id>
# ─────────────────────────────────────────────────────────────────────────────
# ── GET /api/people/<uploaded_tree_id> ─────────────────────────────────────
@people_routes.route("/<string:uploaded_tree_id>", methods=["GET"])
@debug_route
def get_people(uploaded_tree_id: str):
    try:
        parsed = parse_uuid_arg_or_400("uploaded_tree_id", uploaded_tree_id)
        if isinstance(parsed, tuple):  # 🚨 means it returned a (json, code)
            return parsed
    except Exception:
        return jsonify({"error": "tree not found"}), 404

    try:
        with next(get_db()) as db:
            latest_tv, code = _get_latest_version(db, parsed)
            if latest_tv is None:
                msg = "tree not found" if code == 404 else "tree_version lookup failed"
                return jsonify({"error": msg}), code

            limit, offset = _validated_pagination()
            person_query = request.args.get("person", "").strip()

            q = (db.query(Individual.id,
                          Individual.first_name,
                          Individual.last_name,
                          Individual.occupation)
                   .filter(Individual.tree_id == latest_tv.id))

            if person_query:
                term = f"%{person_query}%"
                q = q.filter(or_(Individual.first_name.ilike(term),
                                 Individual.last_name.ilike(term)))

            total = q.count()
            rows  = (q.order_by(Individual.last_name, Individual.first_name)
                       .limit(limit).offset(offset).all())

            results = [{
                "id": r.id,
                "name": f"{(r.first_name or '').strip()} {(r.last_name or '').strip()}".strip() or "Unnamed",
                "occupation": r.occupation or None,
            } for r in rows]

            return jsonify({
                "total": total, "count": len(results),
                "limit": limit, "offset": offset,
                "people": results,
            }), 200
    except Exception:
        log.exception("❌ [GET /api/people] unexpected failure")
        return jsonify({"error": "internal"}), 500

# ── POST /api/people/<uploaded_tree_id> ────────────────────────────────────
@people_routes.route("/<string:uploaded_tree_id>", methods=["POST"])
@debug_route
def create_person(uploaded_tree_id: str):
    parsed = parse_uuid_arg_or_400("uploaded_tree_id", uploaded_tree_id)
    if isinstance(parsed, tuple):
        return parsed
    payload = request.get_json(silent=True) or {}

    try:
        with next(get_db()) as db:
            latest_tv, code = _get_latest_version(db, parsed)
            if latest_tv is None:
                msg = "tree not found" if code == 404 else "tree_version lookup failed"
                return jsonify({"error": msg}), code

            payload["tree_id"] = latest_tv.id
            payload.pop("id", None)

            person = Individual(**payload)
            db.add(person); db.commit(); db.refresh(person)

            return jsonify(person.serialize()), 201

    except IntegrityError as ie:
        db.rollback()
        return jsonify({"error": str(ie.orig)}), 400
    except Exception:
        db.rollback()
        log.exception("❌ [POST /api/people] unexpected failure")
        return jsonify({"error": "internal"}), 500
