#!/usr/bin/env python3
"""
Load unresolved_locations.json, apply manual fixes or geocode retries,
and update the database. Supports optional --tree filtering.
"""

import sys
import os
import json
import logging
import shutil
import argparse
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import sessionmaker

from backend.db import get_engine
from backend.models import location_models as models
from backend.services.geocode import Geocode
from backend.services.location_processor import log_unresolved_location
from backend.utils.helpers import normalize_location
from backend.utils.logger import get_file_logger
from backend.config import DATA_DIR

logger = get_file_logger("fix_and_retry")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# ─── Paths Config ───────────────────────────────────────────────────────────
DATA_DIR = Path(DATA_DIR)
DATA_DIR.mkdir(exist_ok=True, parents=True)
UNRESOLVED_LOG = DATA_DIR / "unresolved_locations.json"
DEFAULT_FIXES = DATA_DIR / "manual_place_fixes.json"

# ─── Argparse ───────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--manual_fixes", type=str, default=str(DEFAULT_FIXES),
                    help="Path to manual_place_fixes.json")
parser.add_argument("--tree", type=str,
                    help="Optional: only retry entries from this tree ID")
args = parser.parse_args()

def load_unresolved():
    if not UNRESOLVED_LOG.exists():
        logger.error(f"❌ {UNRESOLVED_LOG} not found.")
        return []
    with open(UNRESOLVED_LOG, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse {UNRESOLVED_LOG}: {e}")
            return []
    logger.info(f"📄 Loaded {len(data)} unresolved entries from {UNRESOLVED_LOG.name}.")
    return data

def load_manual_fixes(path):
    path = Path(path)
    if not path.exists():
        logger.error(f"❌ Manual fixes file not found: {path}")
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def apply_manual_fixes():
    unresolved = load_unresolved()
    fixes = load_manual_fixes(args.manual_fixes)
    if not unresolved:
        logger.info("🟡 No unresolved entries to process.")
        return

    if args.tree:
        before = len(unresolved)
        unresolved = [e for e in unresolved if e.get("tree_id") == args.tree]
        logger.info(f"🌳 Tree filter: {args.tree} → {len(unresolved)} entries (of {before})")

    # Backup unresolved log
    if UNRESOLVED_LOG.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = UNRESOLVED_LOG.with_name(UNRESOLVED_LOG.name + f".bak.{timestamp}")
        shutil.copyfile(UNRESOLVED_LOG, backup_path)
        logger.info(f"📦 Backup of unresolved log saved to: {backup_path}")

    logger.info(f"🔧 Applying manual fixes to {len(unresolved)} entries…")
    still_unresolved = []

    engine = get_engine()
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    geocoder = Geocode(api_key=os.getenv("GEOCODE_API_KEY"))

    for entry in unresolved:
        raw = entry.get("raw_name") or entry.get("place")
        if not raw:
            logger.warning(f"⏭️ Skipping: no raw_name/place → {entry}")
            continue

        norm = normalize_location(raw)
        fix = fixes.get(raw) or fixes.get(norm)
        logger.debug(f"Checking fix for '{raw}' (norm: {norm}): {fix}")

        if fix:
            session = Session()
            try:
                logger.info(f"✅ Applying fix for '{raw}' → {fix}")
                if fix.get("lat") is not None and fix.get("lng") is not None:
                    loc_out = {
                        "raw_name": raw,
                        "normalized_name": fix.get("normalized_name") or fix.get("modern_equivalent") or norm,
                        "latitude": fix["lat"],
                        "longitude": fix["lng"],
                        "confidence_score": float(fix.get("confidence", 1.0)),
                        "confidence_label": "manual",
                        "status": "manual",
                        "source": "manual"
                    }
                    loc = session.query(models.Location).filter_by(normalized_name=loc_out["normalized_name"]).first()
                    if not loc:
                        loc = models.Location(**loc_out)
                        session.add(loc)
                        session.commit()

                    # Log resolved status (for audit)
                    log_unresolved_location(
                        raw,
                        reason="manual_fix_applied",
                        tree_id=entry.get("tree_id")
                    )
                else:
                    logger.warning(f"⚠️ Missing lat/lng for '{raw}' — skipping insert.")
            except Exception:
                session.rollback()
                logger.exception(f"❌ Failed to apply fix for '{raw}'")
                still_unresolved.append(entry)
            finally:
                session.close()
        else:
            logger.debug(f"🛑 No manual fix for '{raw}'")
            still_unresolved.append(entry)

    logger.info(f"✅ Done. {len(unresolved) - len(still_unresolved)} fixed, {len(still_unresolved)} unresolved remain.")

if __name__ == "__main__":
    apply_manual_fixes()
