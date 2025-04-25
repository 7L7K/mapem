# os.path.expanduser("~")/mapem/backend/routes/trees.py
from flask import Blueprint, jsonify, request, current_app as app
from sqlalchemy import func
import json, logging

from backend.db import get_db
from backend.models import (
    TreeVersion,
    Individual,
    Family,
    Event,
)
from backend.services.query_builders import build_event_query

tree_routes = Blueprint("trees", __name__, url_prefix="/api/trees")
logger = logging.getLogger("mapem")

# ────────────────────────────────────────────────────────────────
# 🌳  List Latest Version of Each Tree
# ────────────────────────────────────────────────────────────────
@tree_routes.route("/", methods=["GET"], strict_slashes=False)
def list_trees():
    db = next(get_db())
    try:
        subq = (
            db.query(
                TreeVersion.tree_name,
                func.max(TreeVersion.id).label("max_id")
            )
            .group_by(TreeVersion.tree_name)
            .subquery()
        )

        latest_versions = (
            db.query(TreeVersion)
            .join(subq, TreeVersion.id == subq.c.max_id)
            .order_by(TreeVersion.created_at.desc())
            .all()
        )

        tree_list = [
            {
                "id": tv.id,
                "name": tv.tree_name,
                "uploaded_tree_id": tv.uploaded_tree_id,
                "created_at": tv.created_at.isoformat() if tv.created_at else None,
            }
            for tv in latest_versions
        ]
        return jsonify(tree_list), 200

    except Exception as e:
        logger.exception("🔥 list_trees failed")
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()

# ────────────────────────────────────────────────────────────────
# 🌳  Get Single Tree Version
# ────────────────────────────────────────────────────────────────
@tree_routes.route("/<int:tree_id>", methods=["GET"], strict_slashes=False)
def get_tree(tree_id):
    db = next(get_db())
    try:
        tree = db.query(TreeVersion).filter(TreeVersion.id == tree_id).first()
        if not tree:
            return jsonify({"error": "Tree not found"}), 404

        return jsonify(
            {
                "id": tree.id,
                "uploaded_tree_id": tree.uploaded_tree_id,
                "name": tree.tree_name,
                "created_at": tree.created_at.isoformat() if tree.created_at else None,
            }
        ), 200

    except Exception as e:
        logger.exception("🔥 get_tree failed")
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()

# ────────────────────────────────────────────────────────────────
# 📊  Unfiltered Counts
# ────────────────────────────────────────────────────────────────
@tree_routes.route("/<int:tree_id>/counts", methods=["GET"], strict_slashes=False)
def tree_counts(tree_id):
    db = next(get_db())
    try:
        total_people = db.query(Individual).filter_by(tree_id=tree_id).count()
        total_families = db.query(Family).filter_by(tree_id=tree_id).count()

        return jsonify(
            {
                "totalPeople": total_people,
                "totalFamilies": total_families,
            }
        ), 200

    except Exception as e:
        logger.exception("🔥 tree_counts failed")
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()

# ────────────────────────────────────────────────────────────────
# 👀  Visible Counts with Filters
# ────────────────────────────────────────────────────────────────
@tree_routes.route("/<int:tree_id>/visible-counts", methods=["GET"], strict_slashes=False)
def visible_counts(tree_id):
    db = next(get_db())
    try:
        filters = json.loads(request.args.get("filters", "{}") or "{}")
        logger.debug(f"📦 Filters received: {filters}")

        ev_q = build_event_query(db, tree_id, filters)

        ind_ids = {row[0] for row in ev_q.with_entities(Event.individual_id).all() if row[0]}
        fam_ids = {row[0] for row in ev_q.with_entities(Event.family_id).all() if row[0]}

        return jsonify(
            {
                "people": len(ind_ids),
                "families": len(fam_ids),
            }
        ), 200

    except Exception as e:
        logger.exception("🔥 visible_counts failed")
        return jsonify({"people": 0, "families": 0, "error": str(e)}), 200

    finally:
        db.close()
