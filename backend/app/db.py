# db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create engine using the DATABASE_URI from settings
engine = create_engine(settings.DATABASE_URI)
SessionLocal = sessionmaker(bind=engine)

def get_db_connection():
    return SessionLocal()

def get_engine():
    return engine
