# /Users/kingal/mapem/backend/app/main.py
from flask import Flask
from flask_cors import CORS
import logging

from .routes import register_routes
from .models import Base
from .config import settings
from .db import get_engine, SessionLocal

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("app")

def create_app():
    app = Flask(__name__)
    
    CORS(app, supports_credentials=True, origins=[
        "http://localhost:5173", "http://127.0.0.1:5173"
    ])
    
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['TRAP_HTTP_EXCEPTIONS'] = True
    app.config['DEBUG'] = settings.DEBUG
    app.config['PORT'] = settings.PORT

    # Use the engine from our centralized db module
    engine = get_engine()
    Base.metadata.create_all(engine)
    app.session_maker = SessionLocal  # type: ignore[attr-defined]

    register_routes(app)

    @app.before_request
    def log_request_info():
        from flask import request
        logger.debug(f"➡️ {request.method} {request.path}")
        logger.debug(f"🔍 Headers: {dict(request.headers)}")
        logger.debug(f"🧠 Body: {request.get_data()}")

    return app
