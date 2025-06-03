# backend/db.py

import os
from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config import settings

# ─── ENV / Logging Setup ─────────────────────────────────────────────────────
ENV = os.getenv("FLASK_ENV", "production").lower()
SQL_ECHO = ENV in {"development", "dev"}

# ─── Lazy Engine / Session Construction ──────────────────────────────────────
@lru_cache
def get_engine(db_uri: str | None = None):
    uri = db_uri or settings.database_uri
    return create_engine(
        uri,
        echo=SQL_ECHO,
        future=True,
        pool_pre_ping=True
    )

@lru_cache
def get_sessionmaker(db_uri: str | None = None):
    engine = get_engine(db_uri)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# ─── Default Prod Engine / Session ───────────────────────────────────────────
engine = get_engine()
SessionLocal = get_sessionmaker()

# ─── DB Helpers ──────────────────────────────────────────────────────────────
def get_db():
    """Yield a SQLAlchemy session (used in Flask route DI)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_connection():
    """Return a raw DBAPI connection for manual SQL execution"""
    return engine.connect()
