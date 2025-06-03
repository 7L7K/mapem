# os.path.expanduser("~")/mapem/backend/routes/health.py
from flask import Blueprint, jsonify
from backend.utils.debug_routes import debug_route

health_routes = Blueprint("health", __name__, url_prefix="/api")

@health_routes.route("/ping", methods=["GET"])
@debug_route
def ping():
    """Simple health check endpoint."""
    return jsonify({"message": "pong"}), 200
