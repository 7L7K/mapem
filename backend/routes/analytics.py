from flask import Blueprint, jsonify
from sqlalchemy import func
from sqlalchemy.exc import ProgrammingError

from backend.db import SessionLocal
from backend.models import Location, UploadedTree
from backend.models.enums import LocationStatusEnum
from backend.utils.logger import get_file_logger

log = get_file_logger("analytics")
analytics_routes = Blueprint("analytics", __name__, url_prefix="/api/analytics")

@analytics_routes.route("/snapshot", methods=["GET"])
def system_snapshot():
    db    = SessionLocal()
    stats = {}
    try:
        # total
        stats["total_locations"] = db.query(func.count(Location.id)).scalar() or 0
        # by enum
        stats["resolved"]   = db.query(func.count(Location.id)).filter(Location.status == LocationStatusEnum.ok).scalar() or 0
        stats["unresolved"] = db.query(func.count(Location.id)).filter(Location.status == LocationStatusEnum.unresolved).scalar() or 0
        stats["manual"]     = db.query(func.count(Location.id)).filter(Location.status == LocationStatusEnum.manual_override).scalar() or 0

        # safe “failed” count
        try:
            stats["failed"] = db.query(func.count(Location.id)).filter(Location.status == LocationStatusEnum.failed).scalar() or 0
        except (AttributeError, ProgrammingError):
            log.warning("`failed` not in enum/DB yet; skipping.")
            stats["failed"] = 0

        # timestamps
        lu = db.query(func.max(UploadedTree.created_at)).scalar()
        lm = db.query(func.max(Location.updated_at)).filter(Location.status == LocationStatusEnum.manual_override).scalar()
        stats["last_upload"]      = lu.isoformat() if lu else None
        stats["last_manual_fix"]  = lm.isoformat() if lm else None

        return jsonify(stats), 200

    finally:
        db.close()
