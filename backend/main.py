# backend/main.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import sys
from backend.routes import register_routes
from backend.models import Base
from backend.config import settings
from backend.db import get_engine, SessionLocal
from backend.routes.heatmap import warmup_heatmap

# ─── Logger Setup ───────────────────────────────────────────────
logger = logging.getLogger("mapem")
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().propagate = True

formatter = logging.Formatter("%(asctime)s — %(levelname)s — %(message)s")

file_handler = logging.FileHandler("flask.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Optional: Capture SQLAlchemy engine warnings too
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

# ─── Flask App Factory ──────────────────────────────────────────
def create_app():
    app = Flask(__name__)
    setattr(app, "session_maker", SessionLocal)

    logger.info("📝 Flask app initializing…", extra={"flush": True})

    # ─── CORS Setup ──────────────────────────────────────────────
    frontend_origin = "http://localhost:5173"
    CORS(app, resources={r"/api/*": {"origins": [frontend_origin]}}, supports_credentials=True)

    # ─── DB Setup ────────────────────────────────────────────────
    engine = get_engine()
    Base.metadata.create_all(engine)

    # ─── Register Blueprints ─────────────────────────────────────
    register_routes(app)

    # ─── Request Logging ─────────────────────────────────────────
    @app.before_request
    def log_request_info():
        logger.debug(f"➡️ {request.method} {request.path}")
        logger.debug(f"🔍 Headers: {dict(request.headers)}")
        body = request.get_data(as_text=True)
        logger.debug(f"🧠 Body: {body[:1000]}" if body else "🧠 Body: [Empty]")

    # ─── Teardown (Session Close Only) ───────────────────────────
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        try:
            db = app.session_maker()
            db.close()
            logger.debug("🧼 DB session closed on teardown")
        except Exception as e:
            logger.warning(f"⚠️ DB teardown failed: {e}")

    # ─── Global Error Handler with Rollback ──────────────────────
    @app.errorhandler(Exception)
    def handle_exception(e):
        try:
            db = app.session_maker()
            db.rollback()
            db.close()
            logger.debug("💥 DB rollback complete")
        except Exception as inner:
            logger.warning(f"⚠️ DB rollback failed: {inner}")
        logger.exception("❌ Unhandled exception")
        return jsonify({"error": str(e)}), 500

    # ─── Health Check Routes ─────────────────────────────────────
    @app.route("/api/ping")
    def api_ping():
        return {"status": "ok"}, 200

    @app.route("/")
    def index():
        return {"message": "MapEm API is running. Try /api/ping or /api/trees"}, 200

    # ─── Heatmap Cache Warmup ────────────────────────────────────
    logger.info("🗺️ Warming up heatmap shapes...")
    warmup_heatmap()

    logger.info(f"✅ Flask app ready on port {settings.PORT}", extra={"flush": True})
    app.logger.setLevel("DEBUG")  # Flask internals

    return app
