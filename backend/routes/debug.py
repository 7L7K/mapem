#os.path.expanduser("~")/mapem/backend/routes/debug.py
from flask import Blueprint, jsonify

debug_routes = Blueprint("debug", __name__)

@debug_routes.route("/debug-cors", methods=["GET", "OPTIONS"])
def debug_cors():
    return jsonify({"message": "CORS is working!"})

@debug_routes.route("/trigger-error")
def trigger_error():
    raise RuntimeError("🔥 Forced error for debug tracing")
