from flask import Flask
from flask_cors import CORS
import logging

from backend.routes import register_routes
from backend.models import Base
from backend.config import settings
from backend.db import get_engine, SessionLocal

# ─── Logger Setup ───────────────────────────────────────────────
logger = logging.getLogger("mapem")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("flask.log")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s — %(levelname)s — %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logging.basicConfig(level=logging.DEBUG)

def create_app():
    app = Flask(__name__)
    setattr(app, "session_maker", SessionLocal)  # Pylance-safe
    
    # Force an early log write so the file gets created
    logger.debug("📝 Flask app initializing… writing to flask.log")
    
    # ─── DEV CORS Setup ─────────────────────────────────────────────
    try:
        CORS(
            app,
            resources={r"/*": {"origins": "*"}},
            supports_credentials=True,
            expose_headers=["Content-Type", "Access-Control-Allow-Origin"],
            allow_headers=["*"],
            methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        )
        logger.info("✅ DEV CORS enabled for all routes & origins")
    except Exception:
        logger.exception("❌ CORS setup failed")
    
    # ─── Config ──────────────────────────────────────────────────────
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['TRAP_HTTP_EXCEPTIONS'] = True
    app.config['DEBUG'] = settings.DEBUG
    app.config['PORT'] = settings.PORT

    # ─── DB Setup ────────────────────────────────────────────────────
    engine = get_engine()
    Base.metadata.create_all(engine)
    
    # ─── Register Routes ─────────────────────────────────────────────
    register_routes(app)
    
    @app.before_request
    def log_request_info():
        from flask import request
        logger.debug(f"➡️ {request.method} {request.path}")
        logger.debug(f"🔍 Headers: {dict(request.headers)}")
        logger.debug(f"🧠 Body: {request.get_data()}")
    
    
    # NEW: API ping endpoint for health checks
    @app.route("/api/ping")
    def api_ping():
        return {"status": "ok"}, 200
    
    @app.route("/")
    def index():
        return {"message": "MapEm API is running. Try /ping or /api/trees"}, 200
    
    logger.info(f"✅ Flask app created and ready on port {settings.PORT}.")
    return app
