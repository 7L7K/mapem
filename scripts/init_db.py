# scripts/init_db.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
from backend.models.base import Base
from backend.db import get_engine
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("init_db")


def main():
    engine = get_engine()
    logger.info("Ensuring PostGIS extension (if Postgres)…")
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    except Exception as e:
        logger.warning("PostGIS extension creation skipped/failed: %s", e)
    logger.info("Dropping and recreating all tables…")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("✅ All tables created successfully.")

if __name__ == "__main__":
    main()
