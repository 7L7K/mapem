# scan_schema.py
import logging
from sqlalchemy import create_engine, inspect
from backend.config import settings
from backend.db import get_engine

 

# Use our central engine created from settings
engine = get_engine()
inspector = inspect(engine)

logger.info("🧠 Scanning your PostgreSQL DB...\n")

for table_name in inspector.get_table_names():
    logger.info("📄 Table: %s", table_name)
    for column in inspector.get_columns(table_name):
        name = column["name"]
        dtype = str(column["type"])
        nullable = column["nullable"]
        default = column.get("default")
        logger.info(
            "   └─ %s (%s)%s%s",
            name,
            dtype,
            " NULLABLE" if nullable else "",
            f" DEFAULT={default}" if default else "",
        )
    logger.info("")
