#os.path.expanduser("~")/mapem/backend/routes/people.py
from flask import Blueprint, request, jsonify
from backend.models import Individual
from backend.db import get_db

people_routes = Blueprint("people", __name__, url_prefix="/api/people")

@people_routes.route("/", methods=["GET"], strict_slashes=False)
def get_people():
    tree_id = request.args.get("tree_id")
    limit = int(request.args.get("limit", 500))

    db = next(get_db())
    try:
        query = db.query(Individual).order_by(Individual.id)
        if tree_id:
            query = query.filter(Individual.tree_id == int(tree_id))
        people = query.limit(limit).all()
        return jsonify([p.to_dict() for p in people])
    finally:
        db.close()
