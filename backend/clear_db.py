# backend/clear_db.py
import logging
from sqlalchemy.sql import text
from backend.db import get_engine, SessionLocal
from backend.models import Base

 

def clear_database():
    engine = get_engine()
    # Drop and recreate all tables
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    clear_database()
    logger.info("✅ Database cleared and re‑initialized")
