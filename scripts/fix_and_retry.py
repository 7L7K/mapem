#!/usr/bin/env python3
"""
Load all unresolved_locations.jsonl, attempt to apply any manual fixes,
and retry geocoding those that now have fixes—logging everything as DEBUG.
Supports optional --tree filtering.
"""

import os
import json
import logging
import shutil
import argparse
from datetime import datetime
from sqlalchemy.orm import sessionmaker

from backend.db import get_engine
from backend.services.geocode import Geocode
from backend.services.location_processor import log_unresolved_location
from backend.utils.helpers import normalize_location

# ─── Config ────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE, "backend", "data")
UNRESOLVED_LOG = os.path.join(DATA_DIR, "unresolved_sample.json")
DEFAULT_FIXES = os.path.join(DATA_DIR, "manual_place_fixes.json")

# ─── Logger Setup ──────────────────────────────────────────────
logger = logging.getLogger("fix_and_retry")
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s | %(levelname)s | %(message)s")

# ─── Argument Parser ───────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument(
    "--manual_fixes",
    type=str,
    default=DEFAULT_FIXES,
    help="Path to manual_place_fixes.json"
)
parser.add_argument(
    "--tree",
    type=str,
    help="Optional: only retry entries from this tree ID"
)
args = parser.parse_args()


def load_unresolved():
    json_path = os.path.join(DATA_DIR, "unresolved_locations.json")
    jsonl_path = UNRESOLVED_LOG

    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    logger.info(f"✅ Loaded unresolved data from JSON array: {json_path}")
                    return data
                else:
                    logger.warning(f"⚠️ Unexpected structure in {json_path}, falling back to .jsonl")
            except json.JSONDecodeError:
                logger.warning(f"⚠️ JSON decode error in {json_path}, falling back to .jsonl")

    if os.path.exists(jsonl_path):
        with open(jsonl_path, "r") as f:
            logger.info(f"📄 Loading unresolved data from JSON Lines: {jsonl_path}")
            lines = []
            for i, line in enumerate(f, 1):
                try:
                    lines.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Skipping malformed JSONL line {i}: {e}")
            return lines

    logger.error("❌ No unresolved data files found.")
    return []


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

    logger.info(f"🔧 Applying manual fixes to {len(unresolved)} unresolved entries…")
    still_unresolved = []

    engine = get_engine()
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    geocoder = Geocode()

    for entry in unresolved:
        raw = entry.get("raw_name") or entry.get("place")
        if not raw:
            logger.warning(f"⏭️ Skipping entry: no raw_name/place → {entry}")
            continue

        norm = normalize_location(raw)
        fix = fixes.get(raw) or fixes.get(norm)
        logger.debug(f"Checking manual fix for '{raw}' (norm: {norm}): {fix}")
        #hejf 
        if fix:
            try:
                logger.info(f"✅ Applying manual fix for '{raw}' → {fix}")
                session = Session()
                # Only insert if lat/lng is present
                if fix.get("lat") is not None and fix.get("lng") is not None:
                    loc_out = {
                        "raw_name": raw,
                        "normalized_name": fix.get("modern_equivalent", raw),
                        "latitude": fix["lat"],
                        "longitude": fix["lng"],
                        "confidence_score": 1.0,
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
                        suggested_fix=fix,
                    )
                else:
                    logger.warning(f"Manual fix missing lat/lng for '{raw}' — NOT inserting.")
            except Exception:
                session.rollback()
                logger.exception(f"❌ Failed to fix '{raw}' — logged and moving on")
                still_unresolved.append(entry)
            finally:
                session.close()
        else:
            logger.debug(f"🛑 No manual fix for '{raw}', leaving unresolved")
            still_unresolved.append(entry)
