# os.path.expanduser("~")/mapem/backend/routes/health.py
from flask import Blueprint, jsonify
from backend.db import get_engine
from backend.utils.debug_routes import debug_route

health_routes = Blueprint("health", __name__, url_prefix="/api")

@health_routes.route("/ping", methods=["GET"])
@debug_route
def ping():
    """Simple health check endpoint."""
    try:
        eng = get_engine()
        # try a light connection/ping
        with eng.connect() as con:
            con.execute("SELECT 1")
        return jsonify({"status": "ok", "db": "up"}), 200
    except Exception:
        return jsonify({"status": "degraded", "db": "down"}), 503


