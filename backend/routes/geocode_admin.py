"""
Admin-side Geocode Dashboard routes
• /admin/geocode/stats
• /admin/geocode/unresolved
• /admin/geocode/fix/<id>
• /admin/geocode/history
• /admin/geocode/retry
• /admin/geocode/fuzzy
• /admin/geocode/export?format=csv|json
"""

from __future__ import annotations

import csv, io, json
from datetime import datetime, timezone
from typing import Literal, Optional

from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
    Response,
    send_file,
)

from backend.models.location_models import Location  # ✅ adjust if your split differs
from backend.models.event_models import Event        # ✅ adjust if path differs
from backend.services.location_processor import process_location
from backend.utils.logger import get_file_logger

logger = get_file_logger("geocode_admin")

bp = Blueprint("geocode_admin", __name__, url_prefix="/admin/geocode")


# ───────────────────────── helpers ──────────────────────────
def _db():
    """Shorthand for a new scoped session"""
    return current_app.session_maker()


def _now_iso():
    return datetime.now(tz=timezone.utc).isoformat()


def _location_stats(session) -> dict:
    """Return high-level counts used by StatsPanel."""
    total = session.query(Location).count()
    resolved = session.query(Location).filter(Location.status == "ok").count()
    unresolved = session.query(Location).filter(Location.status == "unresolved").count()
    manual = session.query(Location).filter(Location.status == "manual_override").count()
    failed = session.query(Location).filter(Location.status == "fail").count()
    return dict(
        total=total,
        resolved=resolved,
        unresolved=unresolved,
        manual_overrides=manual,
        failed=failed,
    )


def _export_locations(session, fmt: Literal["csv", "json"]) -> Response:
    q = (
        session.query(Location)
        .with_entities(
            Location.id,
            Location.raw_name,
            Location.normalized_name,
            Location.latitude,
            Location.longitude,
            Location.status,
            Location.updated_at,
        )
        .order_by(Location.id.asc())
    )
    rows = q.all()

    if fmt == "json":
        payload = [
            dict(
                id=r.id,
                raw_name=r.raw_name,
                normalized=r.normalized_name,
                lat=r.latitude,
                lng=r.longitude,
                status=r.status,
                updated_at=r.updated_at.isoformat() if r.updated_at else None,
            )
            for r in rows
        ]
        return jsonify(payload)

    # CSV
    outfile = io.StringIO()
    writer = csv.writer(outfile)
    writer.writerow(
        ["id", "raw_name", "normalized", "lat", "lng", "status", "updated_at"]
    )
    for r in rows:
        writer.writerow(
            [
                r.id,
                r.raw_name,
                r.normalized_name,
                r.latitude,
                r.longitude,
                r.status,
                r.updated_at.isoformat() if r.updated_at else "",
            ]
        )
    mem = io.BytesIO(outfile.getvalue().encode())
    return send_file(
        mem,
        as_attachment=True,
        download_name=f"geocode_export_{datetime.utcnow():%Y%m%d_%H%M%S}.{fmt}",
        mimetype="text/csv",
    )


# ───────────────────────── routes ──────────────────────────
@bp.route("/stats")
def stats():
    """GET → dict of high-level counts."""
    with _db() as session:
        data = _location_stats(session)
    # optional: last upload timestamp (placeholder None)
    data["last_upload"] = None
    return jsonify(data)


@bp.route("/unresolved")
def unresolved():
    """GET → list of unresolved locations + event counts."""
    with _db() as session:
        subquery = (
            session.query(
                Event.location_id.label("loc_id"),
                Event.id.label("e_id"),
            )
            .subquery()
        )
        rows = (
            session.query(
                Location,
                session.query(Event)
                .filter(Event.location_id == Location.id)
                .count()
                .label("event_count"),
            )
            .filter(Location.status == "unresolved")
            .all()
        )

        payload = [
            dict(
                id=loc.id,
                raw_name=loc.raw_name,
                normalized=loc.normalized_name,
                confidence=loc.confidence_label,
                event_count=event_count,
                last_seen=loc.updated_at or loc.created_at,
            )
            for loc, event_count in rows
        ]
    return jsonify(payload)


@bp.route("/fix/<int:loc_id>", methods=["POST"])
def manual_fix(loc_id: int):
    """POST lat/lng → mark location as manual_override."""
    data = request.get_json(force=True)
    lat, lng = data.get("lat"), data.get("lng")
    username = request.headers.get("X-User", "admin")

    if lat is None or lng is None:
        return jsonify({"error": "lat & lng required"}), 400

    with _db() as session:
        loc: Optional[Location] = session.get(Location, loc_id)
        if not loc:
            return jsonify({"error": "location not found"}), 404

        loc.latitude = float(lat)
        loc.longitude = float(lng)
        loc.status = "manual_override"
        loc.updated_at = datetime.utcnow()
        loc.meta = {**(loc.meta or {}), "fixed_by": username}
        session.commit()

        logger.info("🛠️  Manual fix %s by %s → (%.6f,%.6f)", loc.raw_name, username, lat, lng)
        return jsonify({"ok": True})


@bp.route("/history")
def history():
    """GET → list of all manual overrides."""
    with _db() as session:
        rows = (
            session.query(Location)
            .filter(Location.status == "manual_override")
            .order_by(Location.updated_at.desc())
            .all()
        )
        payload = [
            dict(
                id=l.id,
                raw_name=l.raw_name,
                lat=l.latitude,
                lng=l.longitude,
                fixed_by=(l.meta or {}).get("fixed_by", "unknown"),
                date=l.updated_at,
            )
            for l in rows
        ]
    return jsonify(payload)


@bp.route("/retry", methods=["POST"])
def retry_all():
    """Attempt to re-geocode every unresolved location (sync, lightweight)."""
    processed, resolved = 0, 0
    with _db() as session:
        unresolved = (
            session.query(Location).filter(Location.status == "unresolved").all()
        )

        for loc in unresolved:
            processed += 1
            new_loc = process_location(loc.raw_name, db_session=session)
            if new_loc and new_loc.status == "ok":
                resolved += 1

        session.commit()

    return jsonify({"processed": processed, "resolved": resolved})


@bp.route("/fuzzy", methods=["POST"])
def run_fuzzy():
    """Very naive fuzzy-match pass that normalizes names & checks duplicates."""
    with _db() as session:
        # simple example—drop-in for RapidFuzz later
        from backend.utils.helpers import normalize_location

        fixes = 0
        for loc in session.query(Location).filter(Location.status == "unresolved"):
            norm = normalize_location(loc.raw_name)
            dup = (
                session.query(Location)
                .filter(Location.normalized_name == norm, Location.status == "ok")
                .first()
            )
            if dup:
                loc.latitude = dup.latitude
                loc.longitude = dup.longitude
                loc.status = "manual_override"
                fixes += 1
        session.commit()
    return jsonify({"fixed": fixes})


@bp.route("/export")
def export():
    """CSV or JSON export of every location row."""
    fmt: str = request.args.get("format", "json").lower()
    if fmt not in {"csv", "json"}:
        return jsonify({"error": "format must be csv or json"}), 400
    with _db() as session:
        return _export_locations(session, fmt)  # Response object
