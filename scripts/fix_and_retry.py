#!/usr/bin/env python3
"""
Load unresolved_locations.json, apply manual fixes or geocode retries,
and update the database. Supports optional --tree filtering.
"""

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import logging
import shutil
import argparse
from datetime import datetime
from sqlalchemy.orm import sessionmaker

from backend.db import get_engine
from backend.models import location_models as models
from backend.services.geocode import Geocode
from backend.services.location_processor import log_unresolved_location
from backend.utils.helpers import normalize_location
from backend.utils.logger import get_file_logger  # ✅ this line

logger = get_file_logger("fix_and_retry")  # ✅ sets up file logging


# ─── Config ──────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE, "backend", "data")
UNRESOLVED_LOG = os.path.join(DATA_DIR, "unresolved_locations.json")
DEFAULT_FIXES = os.path.join(DATA_DIR, "manual_place_fixes.json")

# ─── Logger Setup ────────────────────────────────────────────────
logger = logging.getLogger("fix_and_retry")
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s | %(levelname)s | %(message)s")

# ─── Argument Parser ─────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--manual_fixes", type=str, default=DEFAULT_FIXES,
                    help="Path to manual_place_fixes.json")
parser.add_argument("--tree", type=str,
                    help="Optional: only retry entries from this tree ID")
args = parser.parse_args()


def load_unresolved():
    if not os.path.exists(UNRESOLVED_LOG):
        logger.error("❌ unresolved_locations.json not found.")
        return []
    with open(UNRESOLVED_LOG, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error("❌ Failed to parse unresolved_locations.json: %s", e)
            return []
    logger.info(f"📄 Loaded {len(data)} unresolved entries from JSON.")
    return data


def load_manual_fixes(path):
    if not os.path.exists(path):
        logger.error(f"❌ Manual fixes file not found: {path}")
        return {}
    with open(path) as f:
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
    if os.path.exists(UNRESOLVED_LOG):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = UNRESOLVED_LOG + f".bak.{timestamp}"
        shutil.copyfile(UNRESOLVED_LOG, backup_path)
        logger.info(f"📦 Backup of unresolved log saved to: {backup_path}")

    logger.info(f"🔧 Applying manual fixes to {len(unresolved)} entries…")
    still_unresolved = []

    engine = get_engine()
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    geocoder = Geocode()

    for entry in unresolved:
        raw = entry.get("raw_name") or entry.get("place")
        if not raw:
            logger.warning(f"⏭️ Skipping: no raw_name/place → {entry}")
            continue

        norm = normalize_location(raw)
        fix = fixes.get(raw) or fixes.get(norm)
        logger.debug(f"Checking fix for '{raw}' (norm: {norm}): {fix}")

        if fix:
            try:
                logger.info(f"✅ Applying fix for '{raw}' → {fix}")
                session = Session()

                if fix.get("lat") is not None and fix.get("lng") is not None:
                    loc_out = {
                        "raw_name": raw,
                        "normalized_name": fix.get("modern_equivalent", norm),
                        "latitude": fix["lat"],
                        "longitude": fix["lng"],
                        "confidence_score": fix.get("confidence", 1.0),
                        "confidence_label": "manual",
                        "status": "manual",
                        "source": "manual"
                    }
                    loc = session.query(models.Location).filter_by(normalized_name=loc_out["normalized_name"]).first()
                    if not loc:
                        loc = models.Location(**loc_out)
                        session.add(loc)
                        session.commit()

                    log_unresolved_location(
                        raw_name=raw,
                        reason="manual_fix_applied",
                        status="fixed",
                        source_tag="manual_retry",
                        suggested_fix=f"{loc_out['latitude']},{loc_out['longitude']}",
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


# ─── Entry Point ─────────────────────────────────────────────────
if __name__ == "__main__":
    apply_manual_fixes()
