from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from backend.utils.logger import get_logger
from backend.routes import register_routes
from backend.models import Base
from backend.config import settings
from backend.utils.logger import get_logger
from backend.db import get_engine, SessionLocal
from backend.routes.heatmap import warmup_heatmap

# ─── Logger Setup ───────────────────────────────────────────────
logger = get_logger(__name__)

formatter = logging.Formatter("%(asctime)s — %(levelname)s — %(message)s")

file_handler = logging.FileHandler("flask.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Optional: Capture SQLAlchemy engine warnings too
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

# ─── Flask App Factory ──────────────────────────────────────────
def create_app():
    engine = get_engine()  # Get the engine FIRST so we can inspect it/log it
    print(f"🧪 USING DB URL: {engine.url}")

    app = Flask(__name__)
    setattr(app, "session_maker", SessionLocal)

    logger.info("📝 Flask app initializing…", extra={"flush": True})

    # ─── CORS Setup ──────────────────────────────────────────────
    frontend_origin = "http://localhost:5173"
    CORS(app, resources={r"/api/*": {"origins": [frontend_origin]}}, supports_credentials=True)

    # ─── DB Setup ────────────────────────────────────────────────
    # Only create tables if not in test mode
    if not app.config.get("TESTING", False):
        print("🛠 Creating all tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created.")

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

    # Health check and index provided by blueprints (`health`) and here root only
    @app.route("/")
    def index():
        return {"message": "MapEm API is running. Try /api/analytics/snapshot or /api/upload"}, 200

    # ─── Heatmap Cache Warmup ────────────────────────────────────
    logger.info("🗺️ Warming up heatmap shapes...")
    warmup_heatmap()

    logger.info(f"✅ Flask app ready on port {settings.PORT}", extra={"flush": True})
    app.logger.setLevel("DEBUG")  # Flask internals

    return app
