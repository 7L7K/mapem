#!/usr/bin/env python3
# /Users/kingal/mapem/scripts/backfill_individuals_name_parts.py

import os
import json
import logging
from datetime import datetime

from sqlalchemy.orm import sessionmaker
from backend.db import get_engine
from backend.models import Individual
from backend.utils.helpers import split_full_name

# ─── Config ──────────────────────────────────────────────────────
LOG_PATH = "backend/data/backfill_name_log.jsonl"
DRY_RUN = True  # ← flip to False to actually commit

# ─── Logger Setup ────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backfill_names")

# ─── Logging Function ────────────────────────────────────────────
def log_backfill(ind_id, name, first, last):
    entry = {
        "id": ind_id,
        "original_name": name,
        "first_name": first,
        "last_name": last,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

# ─── Main Backfill Function ──────────────────────────────────────
def backfill_names():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    logger.info("🔍 Scanning individuals missing first/last name...")
    individuals = (
        session.query(Individual)
        .filter((Individual.first_name == None) | (Individual.last_name == None))
        .all()
    )
    logger.info(f"🧾 Found {len(individuals)} to backfill")

    updated = 0
    for ind in individuals:
        if not ind.name:
            continue

        first, last = split_full_name(ind.name)
        if first or last:
            ind.first_name = first
            ind.last_name = last
            log_backfill(ind.id, ind.name, first, last)
            updated += 1

    logger.info(f"📌 Processed {updated} individuals.")

    if DRY_RUN:
        logger.warning("🧪 Dry run mode — no DB commit.")
        session.rollback()
    else:
        logger.info("✅ Committing changes to DB...")
        session.commit()

if __name__ == "__main__":
    backfill_names()
