from __future__ import annotations

from flask import Blueprint, jsonify
from sqlalchemy import func

from backend.db import SessionLocal
from backend.models import Location, UploadedTree
from backend.models.enums import LocationStatusEnum

analytics_routes = Blueprint("analytics", __name__, url_prefix="/api/analytics")

@analytics_routes.route("/snapshot", methods=["GET"])
def system_snapshot():
    db = SessionLocal()
    try:
        total = db.query(func.count(Location.id)).scalar() or 0
        resolved = (
            db.query(func.count(Location.id))
            .filter(Location.status == LocationStatusEnum.ok)
            .scalar()
            or 0
        )
        unresolved = (
            db.query(func.count(Location.id))
            .filter(Location.status == LocationStatusEnum.unresolved)
            .scalar()
            or 0
        )
        manual = (
            db.query(func.count(Location.id))
            .filter(Location.status == LocationStatusEnum.manual_override)
            .scalar()
            or 0
        )
        # not all schemas may have a "fail" status
        failed = (
            db.query(func.count(Location.id))
            .filter(Location.status == "fail")
            .scalar()
            or 0
        )

        last_upload = db.query(func.max(UploadedTree.created_at)).scalar()
        last_manual_fix = (
            db.query(func.max(Location.updated_at))
            .filter(Location.status == LocationStatusEnum.manual_override)
            .scalar()
        )

        return (
            jsonify(
                {
                    "total_locations": total,
                    "resolved": resolved,
                    "unresolved": unresolved,
                    "manual_fixes": manual,
                    "failed": failed,
                    "last_upload": last_upload.isoformat() if last_upload else None,
                    "last_manual_fix": last_manual_fix.isoformat() if last_manual_fix else None,
                }
            ),
            200,
        )
    finally:
        db.close()
