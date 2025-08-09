from __future__ import annotations

from flask import Blueprint, jsonify, request
from celery.result import AsyncResult

from backend.db import SessionLocal
from backend.models import Job

jobs_routes = Blueprint("jobs", __name__, url_prefix="/api/jobs")


@jobs_routes.get("/<string:job_id>")
def job_detail(job_id: str):
    with SessionLocal.begin() as session:
        job = session.get(Job, job_id)
        if not job:
            return jsonify({"error": "not found"}), 404
        status = job.status
        if job.task_id:
            try:
                ar = AsyncResult(job.task_id)
                status = ar.state.lower()
            except Exception:
                pass
        return jsonify({
            "id": str(job.id),
            "task_id": job.task_id,
            "type": job.job_type,
            "status": status,
            "progress": job.progress,
            "params": job.params,
            "result": job.result,
            "error": job.error,
        })


@jobs_routes.get("/")
def list_jobs():
    status = request.args.get("status")
    job_type = request.args.get("type")
    with SessionLocal.begin() as session:
        q = session.query(Job)
        if status:
            q = q.filter(Job.status == status)
        if job_type:
            q = q.filter(Job.job_type == job_type)
        rows = q.order_by(Job.created_at.desc()).limit(200).all()
        return jsonify([
            {
                "id": str(j.id),
                "task_id": j.task_id,
                "type": j.job_type,
                "status": j.status,
                "progress": j.progress,
                "created_at": j.created_at.isoformat(),
            }
            for j in rows
        ])

