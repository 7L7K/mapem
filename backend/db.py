# db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config import settings
from backend.models import Base
import os

# Create engine using the DATABASE_URI from settings
engine = create_engine(settings.database_uri)
SessionLocal = sessionmaker(bind=engine)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://kingal@localhost:5432/genealogy_db")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def get_session():
    return SessionLocal()

def get_db_connection():
    return SessionLocal()

def get_engine():
    return engine
