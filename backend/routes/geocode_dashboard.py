"""Admin dashboard for geocode statistics and manual fixes."""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
from sqlalchemy import func, text
from pathlib import Path
import json
from datetime import datetime

from backend.db import SessionLocal
from backend.models.location import Location
from backend.models.enums import LocationStatusEnum
from backend.utils.logger import get_file_logger
from backend.config import DATA_DIR
from backend.utils.helpers import normalize_location

logger = get_file_logger("geocode_dashboard")

geocode_dashboard = Blueprint(
    "geocode_dashboard",
    __name__,
    url_prefix="/admin/geocode",
    template_folder="../templates",
)

FIXES_PATH = Path(DATA_DIR) / "manual_place_fixes.json"
HISTORY_PATH = Path(DATA_DIR) / "manual_place_fixes_history.json"


@geocode_dashboard.route("/", methods=["GET"], strict_slashes=False)
def show_dashboard():
    """Display simple geocode statistics."""
    db = SessionLocal()
    try:
        stats = (
            db.query(Location.status, func.count(Location.id))
            .group_by(Location.status)
            .all()
        )
        stats_dict = {str(status): count for status, count in stats}
        history = []
        if HISTORY_PATH.exists():
            try:
                with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                logger.exception("Failed to load %s", HISTORY_PATH)
    finally:
        db.close()
    return render_template("geocode_dashboard.html", stats=stats_dict, history=history)


@geocode_dashboard.route("/manual-fix", methods=["POST"], strict_slashes=False)
def manual_fix():
    """Apply a simple manual latitude/longitude override."""
    loc_id = request.form.get("id", type=int)
    lat = request.form.get("lat", type=float)
    lng = request.form.get("lng", type=float)
    source = request.form.get("source", "admin_dashboard")

    if not loc_id or lat is None or lng is None:
        logger.warning("⚠️ manual_fix missing parameters")
        return redirect(url_for("geocode_dashboard.show_dashboard"))

    db = SessionLocal()
    try:
        loc = db.query(Location).get(loc_id)
        if loc:
            loc.latitude = lat
            loc.longitude = lng
            loc.status = LocationStatusEnum.manual_override
            loc.source = source
            db.commit()
            logger.info("🔧 manual override applied to location %s", loc_id)

            # update manual_place_fixes.json
            key = normalize_location(loc.raw_name) or loc.normalized_name
            try:
                fixes = {}
                if FIXES_PATH.exists():
                    with open(FIXES_PATH, "r", encoding="utf-8") as f:
                        fixes = json.load(f)
            except Exception:
                logger.exception("Failed to load %s", FIXES_PATH)
                fixes = {}

            fixes[key] = {
                "modern_equivalent": loc.raw_name,
                "lat": lat,
                "lng": lng,
                "source": source,
            }

            with open(FIXES_PATH, "w", encoding="utf-8") as f:
                json.dump(fixes, f, indent=2)

            # append history entry
            history = []
            if HISTORY_PATH.exists():
                try:
                    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                        history = json.load(f)
                except Exception:
                    logger.exception("Failed to load %s", HISTORY_PATH)
                    history = []

            history.append(
                {
                    "id": loc_id,
                    "raw_name": loc.raw_name,
                    "lat": lat,
                    "lng": lng,
                    "fixed_by": source,
                    "date": datetime.utcnow().date().isoformat(),
                }
            )

            with open(HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
        else:
            logger.warning("⚠️ Location %s not found", loc_id)
    except Exception:
        db.rollback()
        logger.exception("💥 failed manual fix")
    finally:
        db.close()

    return redirect(url_for("geocode_dashboard.show_dashboard"))


# ─── Debug JSON endpoints (read-only) ─────────────────────────────────────
@geocode_dashboard.route("/api/attempts", methods=["GET"])
def list_attempts():
    db = current_app.session_maker()
    try:
        rows = db.execute(
            text(
                """
                SELECT id, raw_place, name_norm, provider, score, created_at
                FROM geocode_attempts
                ORDER BY created_at DESC
                LIMIT 200
                """
            )
        ).fetchall()
        data = [dict(r._mapping) for r in rows]
        return jsonify({"data": data, "error": None})
    except Exception as e:
        return jsonify({"data": None, "error": str(e)}), 500
    finally:
        db.close()


@geocode_dashboard.route("/api/gazetteer_stats", methods=["GET"])
def gazetteer_stats():
    db = current_app.session_maker()
    try:
        rows = db.execute(
            text(
                """
                SELECT era_bucket, COUNT(*) AS n
                FROM gazetteer_entries
                GROUP BY era_bucket
                ORDER BY era_bucket
                """
            )
        ).fetchall()
        data = [dict(r._mapping) for r in rows]
        return jsonify({"data": data, "error": None})
    except Exception as e:
        return jsonify({"data": None, "error": str(e)}), 500
    finally:
        db.close()

