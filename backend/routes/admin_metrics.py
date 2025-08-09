from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Dict

from flask import Blueprint, jsonify
from sqlalchemy import text

from backend.db import SessionLocal
from backend.models import Base
from backend.utils.debug_routes import debug_route
from backend.utils.logger import get_file_logger

log = get_file_logger("admin_metrics")
admin_metrics_routes = Blueprint("admin_metrics", __name__, url_prefix="/api/admin/metrics")


def _is_testing() -> bool:
    return bool(os.getenv("PYTEST_CURRENT_TEST"))


@admin_metrics_routes.route("/tables", methods=["GET"])
@debug_route
def table_counts():
    db = SessionLocal()
    try:
        counts: Dict[str, int] = {}
        for table_name in sorted(Base.metadata.tables.keys()):
            try:
                cnt = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar() or 0
                counts[table_name] = int(cnt)
            except Exception:
                counts[table_name] = -1
        return jsonify({"counts": counts}), 200
    finally:
        db.close()


@admin_metrics_routes.route("/recent", methods=["GET"])
@debug_route
def recent_activity():
    db = SessionLocal()
    try:
        def iso(sql: str) -> str | None:
            try:
                val = db.execute(text(sql)).scalar()
                return val.isoformat() if val else None
            except Exception:
                return None

        out = {
            "locations_last_update": iso("SELECT MAX(updated_at) FROM locations"),
            "events_last_update": iso("SELECT MAX(date) FROM events"),
            "individuals_last_update": iso("SELECT MAX(updated_at) FROM individuals"),
            "uploaded_trees_created": iso("SELECT MAX(created_at) FROM uploaded_trees"),
            "tree_versions_created": iso("SELECT MAX(created_at) FROM tree_versions"),
        }
        return jsonify(out), 200
    finally:
        db.close()


@admin_metrics_routes.route("/db", methods=["GET"])
@debug_route
def db_health():
    db = SessionLocal()
    try:
        t0 = time.perf_counter()
        ok = db.execute(text("SELECT 1")).scalar() == 1
        ms = int((time.perf_counter() - t0) * 1000)
        return jsonify({"ok": ok, "latency_ms": ms}), 200
    except Exception as e:
        log.error("db_health failed: %s", e, exc_info=True)
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        db.close()


