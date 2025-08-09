import os
from functools import lru_cache
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from backend.config import settings
from backend.utils.logger import get_file_logger

logger = get_file_logger("db")
ENV = os.getenv("FLASK_ENV", "production").lower()
SQL_ECHO = ENV in {"development", "dev"}

@lru_cache
def get_engine(db_uri: str | None = None):
    # Prefer in-memory SQLite during tests to avoid external dependencies
    if os.getenv("PYTEST_CURRENT_TEST"):
        uri = "sqlite:///:memory:"
    else:
        uri = db_uri or settings.database_uri
    kw = dict(echo=SQL_ECHO, future=True)
    # SQLite in-memory uses SingletonThreadPool; omit pool params
    if not uri.startswith("sqlite:///"):
        kw.update(
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=30,
            pool_timeout=15,
            pool_recycle=1800,
        )
    engine = create_engine(uri, **kw)
    # Debug: log all checkouts/checkins for pool health
    @event.listens_for(engine, "checkout")
    def on_checkout(dbapi_con, con_record, con_proxy):
        logger.debug("🔌 DBPool checkout (con_record=%s)", con_record)

    @event.listens_for(engine, "checkin")
    def on_checkin(dbapi_con, con_record):
        logger.debug("🔌 DBPool checkin (con_record=%s)", con_record)

    return engine

@lru_cache
def get_sessionmaker(db_uri: str | None = None):
    engine = get_engine(db_uri)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

engine = get_engine()
SessionLocal = get_sessionmaker()

def get_db():
    """Yield a SQLAlchemy session (legacy pattern — prefer context managers)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_connection():
    """Return a raw DBAPI connection for manual SQL execution"""
    return engine.connect()
