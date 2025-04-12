from flask import Blueprint, jsonify
from sqlalchemy import func
from app.models import TreeVersion
from app.utils.helpers import get_db_connection

tree_routes = Blueprint("trees", __name__, url_prefix="/api/trees")

@tree_routes.route("/", methods=["GET"])
def list_trees():
    session = get_db_connection()
    try:
        subquery = session.query(
            TreeVersion.tree_name,
            func.max(TreeVersion.id).label("max_id")
        ).group_by(TreeVersion.tree_name).subquery()

        latest_versions = session.query(TreeVersion).join(
            subquery, TreeVersion.id == subquery.c.max_id
        ).order_by(TreeVersion.created_at.desc()).all()

        tree_list = [{"id": t.id, "name": t.tree_name} for t in latest_versions]
        return jsonify(tree_list), 200
    except Exception as e:
        import traceback
        print("🔥 /api/trees failed")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
