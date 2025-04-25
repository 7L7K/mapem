# backend/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config import settings

# Create engine using the DATABASE_URI from settings
engine = create_engine(settings.database_uri, echo=False)
SessionLocal = sessionmaker(bind=engine)

# Unified DB getter — safe for route injection / teardown
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Alias for legacy calls
def get_db_connection():
    return next(get_db())

def get_engine():
    return engine
