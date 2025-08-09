from __future__ import annotations

from flask import Blueprint, jsonify, request
from sqlalchemy import or_, func
from sqlalchemy.orm import load_only

from backend.db import SessionLocal
from backend.models import Individual
from backend.models.dtos import IndividualsQueryDTO
from backend.utils.logger import get_file_logger

logger = get_file_logger("individuals")
individuals_routes = Blueprint("individuals", __name__, url_prefix="/api/individuals")


@individuals_routes.get("")
def search_individuals():
    try:
        dto = IndividualsQueryDTO(
            query=request.args.get("query"),
            version=request.args.get("version"),
            page=request.args.get("page", default=1),
            page_size=request.args.get("page_size", default=50),
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    db = SessionLocal()
    try:
        term = (dto.query or "").strip()
        q = (
            db.query(Individual)
            .filter(Individual.tree_id == dto.version)
            .options(load_only(Individual.id, Individual.first_name, Individual.last_name, Individual.occupation))
        )
        if term:
            like = f"%{term}%"
            q = q.filter(
                or_(
                    Individual.first_name.ilike(like),
                    Individual.last_name.ilike(like),
                )
            )

        total = q.count()
        rows = (
            q.order_by(Individual.last_name.asc(), Individual.first_name.asc())
            .limit(dto.page_size)
            .offset((dto.page - 1) * dto.page_size)
            .all()
        )
        results = [
            {
                "id": str(p.id),
                "name": p.full_name,
                "occupation": p.occupation or None,
            }
            for p in rows
        ]
        return (
            jsonify(
                {
                    "total": total,
                    "count": len(results),
                    "page": dto.page,
                    "page_size": dto.page_size,
                    "people": results,
                }
            ),
            200,
        )
    except Exception as exc:
        logger.exception("/api/individuals failed: %s", exc)
        return jsonify({"error": str(exc)}), 500
    finally:
        db.close()