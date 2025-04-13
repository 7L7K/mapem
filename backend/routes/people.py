from flask import Blueprint, request, jsonify
from backend.models import Individual
from backend.db import get_db_connection

people_routes = Blueprint("people", __name__, url_prefix="/api/people")

@people_routes.route("/", methods=["GET"])
def get_people():
    tree_id = request.args.get("tree_id")
    limit = int(request.args.get("limit", 500))

    session = get_db_connection()
    try:
        query = session.query(Individual).order_by(Individual.id)
        if tree_id:
            query = query.filter(Individual.tree_id == int(tree_id))
        people = query.limit(limit).all()
        return jsonify([p.to_dict() for p in people])
    finally:
        session.close()
