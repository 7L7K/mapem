# scripts/check_models.py

import sys
from pathlib import Path

# 🔧 Add project root to path so "backend" can be imported
sys.path.append(str(Path(__file__).resolve().parents[1]))

import logging
from backend.models import Base
from backend.db import get_engine

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def check_model_tables():
    engine = get_engine()
    metadata = Base.metadata

    logger.info("📦 Checking model table registration...")
    for table_name, table in metadata.tables.items():
        col_count = len(table.columns)
        logger.info(f"✅ {table_name} ({col_count} columns)")

    logger.info("🎯 Model check complete.")

if __name__ == "__main__":
    check_model_tables()
