"""Admin dashboard for geocode statistics and manual fixes."""

from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import func

from backend.db import SessionLocal
from backend.models.location import Location
from backend.models.enums import LocationStatusEnum
from backend.utils.logger import get_file_logger

logger = get_file_logger("geocode_dashboard")

geocode_dashboard = Blueprint(
    "geocode_dashboard",
    __name__,
    url_prefix="/admin/geocode",
    template_folder="../templates",
)


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
    finally:
        db.close()
    return render_template("geocode_dashboard.html", stats=stats_dict)


@geocode_dashboard.route("/manual-fix", methods=["POST"], strict_slashes=False)
def manual_fix():
    """Apply a simple manual latitude/longitude override."""
    loc_id = request.form.get("id", type=int)
    lat = request.form.get("lat", type=float)
    lng = request.form.get("lng", type=float)

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
            db.commit()
            logger.info("🔧 manual override applied to location %s", loc_id)
        else:
            logger.warning("⚠️ Location %s not found", loc_id)
    except Exception:
        db.rollback()
        logger.exception("💥 failed manual fix")
    finally:
        db.close()

    return redirect(url_for("geocode_dashboard.show_dashboard"))

