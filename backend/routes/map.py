from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple

from flask import Blueprint, jsonify, request, abort
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from backend.db import SessionLocal
from backend.models import Event, TreeVersion, UploadedTree, Individual, Location
from backend.models.dtos import MapQueryDTO
from backend.utils.logger import get_file_logger

logger = get_file_logger("map")
map_routes = Blueprint("map", __name__, url_prefix="/api/map")


def _validate_version(db, version_id) -> bool:
    tv = db.get(TreeVersion, version_id)
    return tv is not None


@map_routes.get("")
def get_map():
    # Parse and validate query via Pydantic
    try:
        dto = MapQueryDTO(
            year=request.args.get("year", type=int),
            bbox=request.args.get("bbox"),
            version=request.args.get("version"),
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    db = SessionLocal()
    try:
        if not _validate_version(db, dto.version):
            return jsonify({"error": "version not found"}), 404

        # Base query: events in given year for this tree version
        q = (
            db.query(Event)
            .filter(Event.tree_id == dto.version)
            .filter(func.extract("year", Event.date) == dto.year)
            .options(joinedload(Event.location), joinedload(Event.participants))
        )

        # Optional bbox filter on location coordinates
        bbox: Tuple[float, float, float, float] | None = dto.bbox_tuple()
        if bbox:
            x_min, y_min, x_max, y_max = bbox
            q = q.filter(
                Event.location.has(
                    (Location.longitude >= x_min)
                    & (Location.longitude <= x_max)
                    & (Location.latitude >= y_min)
                    & (Location.latitude <= y_max)
                )
            )

        events: List[Event] = q.all()

        # Cluster by rounded coords to simulate clustering on backend
        clusters: Dict[Tuple[int, int], Dict[str, Any]] = {}
        counts = {"events": 0, "people": 0, "places": 0}
        seen_people = set()
        seen_places = set()

        def bucket(lat: float, lng: float) -> Tuple[int, int]:
            # 2 decimal degrees ≈ ~1.1 km — tweak as needed
            return int(round(lat * 100)), int(round(lng * 100))

        for e in events:
            loc = e.location
            if not loc or loc.latitude is None or loc.longitude is None:
                continue
            key = bucket(float(loc.latitude), float(loc.longitude))
            cluster = clusters.setdefault(
                key,
                {
                    "lat": float(loc.latitude),
                    "lng": float(loc.longitude),
                    "count": 0,
                    "person_ids": set(),
                    "event_types": defaultdict(int),
                },
            )
            cluster["count"] += 1
            cluster["event_types"][e.event_type] += 1
            for p in e.participants:
                cluster["person_ids"].add(p.id)
                seen_people.add(p.id)
            seen_places.add(loc.id)
            counts["events"] += 1

        # Serialize clusters
        features = []
        for (_y, _x), c in clusters.items():
            features.append(
                {
                    "lat": c["lat"],
                    "lng": c["lng"],
                    "count": c["count"],
                    "event_types": dict(c["event_types"]),
                    "unique_people": len(c["person_ids"]),
                }
            )

        counts["people"] = len(seen_people)
        counts["places"] = len(seen_places)

        return jsonify({"clusters": features, "summary": counts}), 200
    except Exception as exc:
        logger.exception("/api/map failed: %s", exc)
        return jsonify({"error": str(exc)}), 500
    finally:
        db.close()