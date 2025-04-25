# backend/main.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

from backend.routes import register_routes
from backend.models import Base
from backend.config import settings
from backend.db import get_engine, SessionLocal
from backend.routes.heatmap import warmup_heatmap

# ─── Logger Setup ───────────────────────────────────────────────
logger = logging.getLogger("mapem")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("flask.log")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s — %(levelname)s — %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logging.basicConfig(level=logging.DEBUG)

# ─── Flask App Factory ──────────────────────────────────────────
def create_app():
    app = Flask(__name__)
    setattr(app, "session_maker", SessionLocal)  # Safe for IDEs / LSPs

    logger.debug("📝 Flask app initializing… writing to flask.log")

    # ─── CORS Setup (Locked Down) ──────────────────────────────────
    frontend_origin = "http://localhost:5173"
    CORS(
        app,
        resources={r"/api/*": {"origins": [frontend_origin]}},
        supports_credentials=True,
        expose_headers=["Content-Type"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # ─── DB & Models Setup ──────────────────────────────────────────
    engine = get_engine()
    Base.metadata.create_all(engine)

    # ─── Register Blueprints ────────────────────────────────────────
    register_routes(app)

    # ─── Request Logging ─────────────────────────────────────────────
    @app.before_request
    def log_request_info():
        logger.debug(f"➡️ {request.method} {request.path}")
        logger.debug(f"🔍 Headers: {dict(request.headers)}")
        body = request.get_data(as_text=True)
        if body and len(body) < 1000:
            logger.debug(f"🧠 Body: {body}")
        else:
            logger.debug("🧠 Body: [Too large or empty]")

    # ─── Health Check ────────────────────────────────────────────────
    @app.route("/api/ping")
    def api_ping():
        return {"status": "ok"}, 200

    @app.route("/")
    def index():
        return {"message": "MapEm API is running. Try /api/ping or /api/trees"}, 200

    # ─── Global Error Handler ────────────────────────────────────────
    @app.errorhandler(Exception)
    def handle_all_errors(e):
        logger.exception("❌ Unhandled exception")
        return jsonify({"error": str(e)}), 500

    # ─── 🔥 Heatmap Warmup (Only Once) ───────────────────────────────
    logger.info("🗺️ Warming up heatmap shapes on first request...")
    warmup_heatmap()

    app.logger.setLevel("DEBUG")
    logger.info(f"✅ Flask app created and ready on port {settings.PORT}.")
    return app
