#os.path.expanduser("~")/mapem/backend/routes/trees.py
from flask import Blueprint, jsonify
from sqlalchemy import func
from backend.models import TreeVersion
from backend.utils.helpers import get_db_connection
from flask import current_app as app  # Add at top if not there


tree_routes = Blueprint("trees", __name__, url_prefix="/api/trees")

@tree_routes.route("/", methods=["GET"], strict_slashes=False)
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

        tree_list = [{
            "id": t.id,
            "name": t.tree_name,
            "uploaded_tree_id": t.uploaded_tree_id
        } for t in latest_versions]

        return jsonify(tree_list), 200

    except Exception as e:
        import traceback
        print("🔥 /api/trees failed")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()


@tree_routes.route("/<int:tree_id>", methods=["GET"])
def get_tree(tree_id):
    session = get_db_connection()
    try:
        tree = session.query(TreeVersion).filter(TreeVersion.id == tree_id).first()
        if not tree:
            return jsonify({"error": "Tree not found"}), 404
        return jsonify({
            "id": tree.uploaded_tree_id,  # 👈 send uploaded ID here
            "name": tree.tree_name,
            "created_at": tree.created_at.isoformat() if tree.created_at else None
        }), 200
    except Exception as e:
        import traceback
        print("🔥 Error in /api/trees/<id>")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
