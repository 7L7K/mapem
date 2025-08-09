from __future__ import annotations

from flask import Blueprint, request, jsonify
from backend.db import SessionLocal
from backend.models import Individual, UserAction
from backend.models.enums import ActionTypeEnum
from backend.utils.debug_routes import debug_route

merge_routes = Blueprint("merge_people", __name__, url_prefix="/api/merge")


@merge_routes.get("/candidates/<string:uploaded_tree_id>")
@debug_route
def merge_candidates(uploaded_tree_id: str):
    """Return naive candidate pairs within a tree for merge consideration.

    Heuristic: same last name (case-insensitive) and first initial match.
    """
    session = SessionLocal()
    try:
        rows = (
            session.query(Individual)
            .filter(Individual.tree_id == uploaded_tree_id)
            .limit(5000)
            .all()
        )
        buckets = {}
        for p in rows:
            key = ((p.last_name or "").strip().lower(), (p.first_name or " ").strip()[:1].lower())
            buckets.setdefault(key, []).append(p)
        pairs = []
        for key, people in buckets.items():
            if len(people) < 2:
                continue
            for i in range(len(people)):
                for j in range(i + 1, len(people)):
                    a, b = people[i], people[j]
                    pairs.append({
                        "a": {"id": str(a.id), "first_name": a.first_name, "last_name": a.last_name},
                        "b": {"id": str(b.id), "first_name": b.first_name, "last_name": b.last_name},
                    })
        return jsonify({"pairs": pairs[:200]}), 200
    finally:
        session.close()


@merge_routes.post("/people")
@debug_route
def merge_people():
    """Merge person B into person A (side-by-side tool will post this).

    Body: {"targetId": uuid, "sourceId": uuid}
    """
    body = request.get_json(force=True)
    target_id = body.get("targetId")
    source_id = body.get("sourceId")
    if not target_id or not source_id or target_id == source_id:
        return jsonify({"error": "bad request"}), 400
    session = SessionLocal()
    try:
        a = session.get(Individual, target_id)
        b = session.get(Individual, source_id)
        if not a or not b:
            return jsonify({"error": "not found"}), 404
        # Simple strategy: move events from B to A, then delete B
        for ev in list(b.events):
            if a not in ev.participants:
                ev.participants.append(a)
        # Audit
        session.add(UserAction(
            uploaded_tree_id=a.tree_id,
            individual_id=a.id,
            action_type=ActionTypeEnum.merge,
            user_name=request.headers.get("X-User", "system"),
            details={"merged": str(b.id), "into": str(a.id)},
        ))
        session.delete(b)
        session.commit()
        return jsonify({"status": "ok", "merged": source_id, "into": target_id}), 200
    except Exception:
        try:
            session.rollback()
        except Exception:
            pass
        return jsonify({"error": "internal"}), 500
    finally:
        session.close()


