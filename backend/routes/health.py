# os.path.expanduser("~")/mapem/backend/routes/health.py
from flask import Blueprint, jsonify

health_routes = Blueprint("health", __name__, url_prefix="/api")

@health_routes.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok"}), 200
