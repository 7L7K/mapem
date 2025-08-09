from __future__ import annotations

from flask import Blueprint, jsonify
from celery.result import AsyncResult

jobs_routes = Blueprint("jobs", __name__, url_prefix="/api/jobs")


@jobs_routes.get("/<task_id>")
def get_job_status(task_id: str):
    res = AsyncResult(task_id)
    return jsonify({"state": res.state, "info": res.info}), 200