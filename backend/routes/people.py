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
from backend.utils.redaction import should_redact_person, redact_name, is_authorized
from backend.utils.uuid_utils import parse_uuid_arg_or_400
from backend.db import get_db
from backend.models import Individual, TreeVersion, UploadedTree
from backend.utils.debug_routes import debug_route
from uuid import UUID as _UUID
from datetime import date
import csv
import io


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

    db = None
    try:
        db = next(get_db())
        latest_tv, code = _get_latest_version(db, parsed)
        if latest_tv is None:
            msg = "tree not found" if code == 404 else "tree_version lookup failed"
            return jsonify({"error": msg}), code

        limit, offset = _validated_pagination()
        person_query = request.args.get("person", "").strip()
        sort = (request.args.get("sort") or "name_asc").lower()
        count_only = (request.args.get("countOnly", "false").lower() == "true")
        tag = (request.args.get("tag") or "").strip().lower()

        q = (db.query(Individual.id,
                      Individual.first_name,
                      Individual.last_name,
                      Individual.birth_date,
                      Individual.death_date,
                      Individual.occupation,
                      Individual.tags)
               .filter(Individual.tree_id == latest_tv.id))

        if person_query:
            term = f"%{person_query}%"
            # Simple ilike OR on name parts; in Postgres we could add pg_trgm index for speed
            q = q.filter(or_(Individual.first_name.ilike(term),
                             Individual.last_name.ilike(term),
                             Individual.occupation.ilike(term)))
        if tag:
            q = q.filter(Individual.tags.ilike(f"%{tag}%"))

        total = q.count()

        # Sorting
        if sort == "name_desc":
            q = q.order_by(Individual.last_name.desc(), Individual.first_name.desc())
        elif sort == "created_at_asc":
            q = q.order_by(Individual.created_at.asc())
        elif sort == "created_at_desc":
            q = q.order_by(Individual.created_at.desc())
        else:
            q = q.order_by(Individual.last_name.asc(), Individual.first_name.asc())

        if count_only:
            return jsonify({
                "total": total, "count": 0,
                "limit": limit, "offset": offset,
                "people": [],
            }), 200

        rows  = q.limit(limit).offset(offset).all()

        authorized = is_authorized(request.headers)
        results = []
        for r in rows:
            name = f"{(r.first_name or '').strip()} {(r.last_name or '').strip()}".strip()
            hide = (not authorized) and should_redact_person(r.birth_date, r.death_date)
            results.append({
                "id": str(r.id),
                "name": redact_name(name) if hide else (name or "Unnamed"),
                "occupation": r.occupation or None,
                "tags": [t for t in (r.tags or "").split(",") if t],
                "redacted": hide,
            })

        return jsonify({
            "total": total, "count": len(results),
            "limit": limit, "offset": offset,
            "people": results,
            "version_id": str(latest_tv.id),
        }), 200
    except Exception:
        log.exception("❌ [GET /api/people] unexpected failure")
        return jsonify({"error": "internal"}), 500
    finally:
        try:
            if db is not None:
                db.close()
        except Exception:
            pass

# ── POST /api/people/<uploaded_tree_id> ────────────────────────────────────
@people_routes.route("/<string:uploaded_tree_id>", methods=["POST"])
@debug_route
def create_person(uploaded_tree_id: str):
    parsed = parse_uuid_arg_or_400("uploaded_tree_id", uploaded_tree_id)
    if isinstance(parsed, tuple):
        return parsed
    payload = request.get_json(silent=True) or {}

    db = None
    try:
        db = next(get_db())
        latest_tv, code = _get_latest_version(db, parsed)
        if latest_tv is None:
            msg = "tree not found" if code == 404 else "tree_version lookup failed"
            return jsonify({"error": msg}), code

        payload["tree_id"] = latest_tv.id
        payload.pop("id", None)

        person = Individual(**payload)
        db.add(person)
        db.commit()
        db.refresh(person)

        return jsonify(person.serialize()), 201

    except IntegrityError as ie:
        try:
            if db is not None:
                db.rollback()
        except Exception:
            pass
        return jsonify({"error": str(ie.orig)}), 400
    except Exception:
        try:
            if db is not None:
                db.rollback()
        except Exception:
            pass
        log.exception("❌ [POST /api/people] unexpected failure")
        return jsonify({"error": "internal"}), 500
    finally:
        try:
            if db is not None:
                db.close()
        except Exception:
            pass


# ── GET / PATCH / DELETE /api/people/<uploaded_tree_id>/<person_id> ─────────
@people_routes.route("/<string:uploaded_tree_id>/<string:person_id>", methods=["GET"])
@debug_route
def get_person(uploaded_tree_id: str, person_id: str):
    # Validate UUIDs
    parsed_tree = parse_uuid_arg_or_400("uploaded_tree_id", uploaded_tree_id)
    if isinstance(parsed_tree, tuple):
        return parsed_tree
    try:
        pid = _UUID(person_id)
    except Exception:
        return jsonify({"error": "person_id must be a valid UUID"}), 400

    db = None
    try:
        db = next(get_db())
        latest_tv, code = _get_latest_version(db, parsed_tree)
        if latest_tv is None:
            msg = "tree not found" if code == 404 else "tree_version lookup failed"
            return jsonify({"error": msg}), code

        person = (
            db.query(Individual)
              .filter(Individual.id == pid, Individual.tree_id == latest_tv.id)
              .first()
        )
        if not person:
            return jsonify({"error": "person not found"}), 404
        return jsonify(person.serialize()), 200
    except Exception:
        log.exception("❌ [GET person] unexpected failure")
        return jsonify({"error": "internal"}), 500
    finally:
        try:
            if db is not None:
                db.close()
        except Exception:
            pass


# ── GET /api/people/<uploaded_tree_id>/export?format=csv ────────────────────
@people_routes.route("/<string:uploaded_tree_id>/export", methods=["GET"])
@debug_route
def export_people(uploaded_tree_id: str):
    parsed = parse_uuid_arg_or_400("uploaded_tree_id", uploaded_tree_id)
    if isinstance(parsed, tuple):
        return parsed

    db = None
    try:
        db = next(get_db())
        latest_tv, code = _get_latest_version(db, parsed)
        if latest_tv is None:
            msg = "tree not found" if code == 404 else "tree_version lookup failed"
            return jsonify({"error": msg}), code

        q = (db.query(Individual.id,
                      Individual.first_name,
                      Individual.last_name,
                      Individual.gender,
                      Individual.birth_date,
                      Individual.death_date,
                      Individual.occupation)
               .filter(Individual.tree_id == latest_tv.id)
               .order_by(Individual.last_name.asc(), Individual.first_name.asc()))

        rows = q.all()

        si = io.StringIO()
        w = csv.writer(si)
        w.writerow(["id","first_name","last_name","gender","birth_date","death_date","occupation"]) 
        for r in rows:
            w.writerow([
                str(r.id), r.first_name or "", r.last_name or "",
                str(r.gender) if r.gender else "",
                r.birth_date.isoformat() if r.birth_date else "",
                r.death_date.isoformat() if r.death_date else "",
                r.occupation or "",
            ])
        out = si.getvalue().encode("utf-8")
        return (
            out,
            200,
            {
                "Content-Type": "text/csv; charset=utf-8",
                "Content-Disposition": "attachment; filename=people.csv",
            },
        )
    except Exception:
        log.exception("❌ [EXPORT people] unexpected failure")
        return jsonify({"error": "internal"}), 500
    finally:
        try:
            if db is not None:
                db.close()
        except Exception:
            pass


# ── POST /api/people/<uploaded_tree_id>/bulk-tags ───────────────────────────
@people_routes.route("/<string:uploaded_tree_id>/bulk-tags", methods=["POST"])
@debug_route
def bulk_tags(uploaded_tree_id: str):
    parsed = parse_uuid_arg_or_400("uploaded_tree_id", uploaded_tree_id)
    if isinstance(parsed, tuple):
        return parsed

    body = request.get_json(silent=True) or {}
    action = (body.get("action") or "").lower()  # add|remove|set
    tag = (body.get("tag") or "").strip().lower()
    ids = body.get("ids") or []

    if action not in {"add", "remove", "set"} or not tag or not isinstance(ids, list):
        return jsonify({"error": "bad request"}), 400

    db = None
    try:
        db = next(get_db())
        latest_tv, code = _get_latest_version(db, parsed)
        if latest_tv is None:
            msg = "tree not found" if code == 404 else "tree_version lookup failed"
            return jsonify({"error": msg}), code

        # Coerce UUIDs
        id_set = set()
        for raw in ids:
            try:
                id_set.add(_UUID(str(raw)))
            except Exception:
                continue
        if not id_set:
            return jsonify({"updated": 0}), 200

        q = db.query(Individual).filter(Individual.tree_id == latest_tv.id, Individual.id.in_(id_set))
        updated = 0
        for person in q.all():
            parts = [t for t in (person.tags or "").split(",") if t]
            if action == "set":
                parts = [tag]
            elif action == "add":
                if tag not in parts:
                    parts.append(tag)
            elif action == "remove":
                parts = [t for t in parts if t != tag]
            person.tags = ",".join(parts)
            updated += 1

        db.commit()
        return jsonify({"updated": updated}), 200
    except Exception:
        try:
            if db is not None:
                db.rollback()
        except Exception:
            pass
        log.exception("❌ [bulk-tags] unexpected failure")
        return jsonify({"error": "internal"}), 500
    finally:
        try:
            if db is not None:
                db.close()
        except Exception:
            pass


@people_routes.route("/<string:uploaded_tree_id>/<string:person_id>", methods=["PATCH"])
@debug_route
def update_person(uploaded_tree_id: str, person_id: str):
    parsed_tree = parse_uuid_arg_or_400("uploaded_tree_id", uploaded_tree_id)
    if isinstance(parsed_tree, tuple):
        return parsed_tree
    try:
        pid = _UUID(person_id)
    except Exception:
        return jsonify({"error": "person_id must be a valid UUID"}), 400

    payload = request.get_json(silent=True) or {}
    allowed = {"first_name", "last_name", "gender", "occupation", "birth_date", "death_date", "tags"}
    updates = {k: v for k, v in payload.items() if k in allowed}

    def _parse_date(val):
        if not val:
            return None
        try:
            return date.fromisoformat(val)
        except Exception:
            return None

    db = None
    try:
        db = next(get_db())
        latest_tv, code = _get_latest_version(db, parsed_tree)
        if latest_tv is None:
            msg = "tree not found" if code == 404 else "tree_version lookup failed"
            return jsonify({"error": msg}), code

        person = db.query(Individual).filter(
            Individual.id == pid, Individual.tree_id == latest_tv.id
        ).first()
        if not person:
            return jsonify({"error": "person not found"}), 404

        if "birth_date" in updates:
            person.birth_date = _parse_date(updates.pop("birth_date"))
        if "death_date" in updates:
            person.death_date = _parse_date(updates.pop("death_date"))
        for k, v in updates.items():
            setattr(person, k, v)

        db.commit()
        db.refresh(person)
        return jsonify(person.serialize()), 200
    except Exception:
        try:
            if db is not None:
                db.rollback()
        except Exception:
            pass
        log.exception("❌ [PATCH person] unexpected failure")
        return jsonify({"error": "internal"}), 500
    finally:
        try:
            if db is not None:
                db.close()
        except Exception:
            pass


@people_routes.route("/<string:uploaded_tree_id>/<string:person_id>", methods=["DELETE"])
@debug_route
def delete_person(uploaded_tree_id: str, person_id: str):
    parsed_tree = parse_uuid_arg_or_400("uploaded_tree_id", uploaded_tree_id)
    if isinstance(parsed_tree, tuple):
        return parsed_tree
    try:
        pid = _UUID(person_id)
    except Exception:
        return jsonify({"error": "person_id must be a valid UUID"}), 400

    db = None
    try:
        db = next(get_db())
        latest_tv, code = _get_latest_version(db, parsed_tree)
        if latest_tv is None:
            msg = "tree not found" if code == 404 else "tree_version lookup failed"
            return jsonify({"error": msg}), code

        person = db.query(Individual).filter(
            Individual.id == pid, Individual.tree_id == latest_tv.id
        ).first()
        if not person:
            return jsonify({"error": "person not found"}), 404
        db.delete(person)
        db.commit()
        return jsonify({"status": "deleted", "id": str(pid)}), 200
    except Exception:
        try:
            if db is not None:
                db.rollback()
        except Exception:
            pass
        log.exception("❌ [DELETE person] unexpected failure")
        return jsonify({"error": "internal"}), 500
    finally:
        try:
            if db is not None:
                db.close()
        except Exception:
            pass


# ── GET /api/people/by-version/<version_id> (strict) ───────────────────────
@people_routes.route("/by-version/<string:version_id>", methods=["GET"])
@debug_route
def get_people_by_version(version_id: str):
    db = None
    try:
        try:
            vid = _UUID(version_id)
        except Exception:
            return jsonify({"error": "version_id must be a valid UUID"}), 400
        db = next(get_db())
        limit, offset = _validated_pagination()
        person_query = request.args.get("person", "").strip()
        sort = (request.args.get("sort") or "name_asc").lower()
        count_only = (request.args.get("countOnly", "false").lower() == "true")
        tag = (request.args.get("tag") or "").strip().lower()

        q = (db.query(Individual.id,
                      Individual.first_name,
                      Individual.last_name,
                      Individual.occupation,
                      Individual.tags)
               .filter(Individual.tree_id == vid))

        if person_query:
            term = f"%{person_query}%"
            q = q.filter(or_(Individual.first_name.ilike(term),
                             Individual.last_name.ilike(term),
                             Individual.occupation.ilike(term)))
        if tag:
            q = q.filter(Individual.tags.ilike(f"%{tag}%"))

        total = q.count()
        if count_only:
            return jsonify({
                "total": total, "count": 0,
                "limit": limit, "offset": offset,
                "people": [],
            }), 200
        if sort == "name_desc":
            q = q.order_by(Individual.last_name.desc(), Individual.first_name.desc())
        elif sort == "created_at_asc":
            q = q.order_by(Individual.created_at.asc())
        elif sort == "created_at_desc":
            q = q.order_by(Individual.created_at.desc())
        else:
            q = q.order_by(Individual.last_name.asc(), Individual.first_name.asc())

        rows = q.limit(limit).offset(offset).all()
        results = [{
            "id": str(r.id),
            "name": f"{(r.first_name or '').strip()} {(r.last_name or '').strip()}".strip() or "Unnamed",
            "occupation": r.occupation or None,
            "tags": [t for t in (r.tags or "").split(",") if t],
        } for r in rows]
        return jsonify({
            "total": total, "count": len(results),
            "limit": limit, "offset": offset,
            "people": results,
            "version_id": str(vid),
        }), 200
    except Exception:
        log.exception("❌ [GET /api/people/by-version] unexpected failure")
        return jsonify({"error": "internal"}), 500
    finally:
        try:
            if db is not None:
                db.close()
        except Exception:
            pass
