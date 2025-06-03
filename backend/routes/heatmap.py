# backend/routes/heatmap.py

import os
import json
import traceback
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import func

from backend.db import get_db
from backend.models import Event, Location, Individual
from backend.utils.debug_routes import debug_route

heatmap_routes = Blueprint("heatmap", __name__, url_prefix="/api/heatmap")

# Caches for GeoJSON shapes
SHAPES_INDEX = {}
SHAPES_LOADED = False
@debug_route

def load_shapes():
    """Load all .geojson files under historical_places/ into SHAPES_INDEX."""
    global SHAPES_LOADED, SHAPES_INDEX
    if SHAPES_LOADED:
        return
    base = os.path.join(os.getcwd(), "backend", "data", "historical_places")
    for root, _, files in os.walk(base):
        for fn in files:
            if fn.lower().endswith(".geojson"):
                path = os.path.join(root, fn)
                try:
                    feat = json.load(open(path))
                    key = feat["properties"]["name"].upper()
                    SHAPES_INDEX[key] = feat
                except Exception as e:
                    current_app.logger.error(f"Failed loading {fn}: {e}")
    SHAPES_LOADED = True

@heatmap_routes.route("/", methods=["GET"], strict_slashes=False)
@debug_route
def get_heatmap():
    """
    Return both pin clusters and optional GeoJSON shapes for a given year + tree(s).
    Optional query params: ?tree_ids=1,2,3&year=1910&surname=Smith
    """
    db = next(get_db())
    try:
        tree_ids = request.args.get("tree_ids", "")
        year = request.args.get("year", "")
        surname = request.args.get("surname", "").upper()

        # Fetch raw counts per location
        heat = {}
        q = db.query(Event, Location).join(Location, Event.location_id == Location.id)
        if tree_ids:
            ids = [int(x) for x in tree_ids.split(",") if x.isdigit()]
            q = q.filter(Event.tree_id.in_(ids))
        if year:
            q = q.filter(func.extract("year", Event.date) == int(year))
        rows = q.all()

        for evt, loc in rows:
            name = loc.name.upper()
            if surname:
                ind = db.query(Individual).filter(
                    Individual.id == evt.individual_id,
                    func.upper(Individual.name).like(f"%{surname}%")
                ).first()
                if not ind:
                    continue
            entry = heat.setdefault(name, {
                "location_name": loc.name,
                "count": 0,
                "tree_counts": {}
            })
            entry["count"] += 1
            entry["tree_counts"][evt.tree_id] = entry["tree_counts"].get(evt.tree_id, 0) + 1

        # Build pins list
        pins = []
        for e in heat.values():
            pins.append(e)

        # Build shapes list
        load_shapes()
        shapes = []
        for pin in pins:
            key = pin["location_name"].upper()
            feat = SHAPES_INDEX.get(key)
            if feat:
                fcopy = feat.copy()
                fcopy["properties"]["count"] = pin["count"]
                fcopy["properties"]["tree_counts"] = pin["tree_counts"]
                shapes.append(fcopy)

        return jsonify({"pins": pins, "shapes": shapes}), 200

    except Exception as e:
        tb = traceback.format_exc()
        current_app.logger.error(f"get_heatmap error: {e}\n{tb}")
        return jsonify({"error": str(e), "trace": tb}), 500

    finally:
        try:
            db.close()
        except:
            pass

@heatmap_routes.route("/events", methods=["GET"], strict_slashes=False)
@debug_route
def get_heatmap_events():
    """
    Drilldown: list distinct individuals for a given location, year & tree.
    Query params: ?location_id=123&year=1910&tree_id=1
    """
    db = next(get_db())
    try:
        loc_id = request.args.get("location_id")
        year   = request.args.get("year")
        tree_id = request.args.get("tree_id")

        q = db.query(Event, Individual, Location) \
              .join(Individual, Event.individual_id == Individual.id) \
              .join(Location, Event.location_id == Location.id)

        if loc_id:
            q = q.filter(Location.id == int(loc_id))
        if year:
            q = q.filter(func.extract("year", Event.date) == int(year))
        if tree_id:
            q = q.filter(Event.tree_id == tree_id)

        rows = q.all()
        persons = []
        seen = set()
        for evt, ind, loc in rows:
            if ind.id in seen:
                continue
            seen.add(ind.id)
            persons.append({
                "person_id": ind.id,
                "name": ind.name,
                "event_type": evt.event_type,
                "date": evt.date.isoformat(),
                "location": loc.name,
                "lat": loc.latitude,
                "lng": loc.longitude,
                "tree_id": evt.tree_id
            })

        return jsonify(persons), 200

    except Exception as e:
        tb = traceback.format_exc()
        current_app.logger.error(f"get_heatmap_events error: {e}\n{tb}")
        return jsonify({"error": str(e), "trace": tb}), 500

    finally:
        try:
            db.close()
        except:
            pass

@debug_route

def warmup_heatmap():
    load_shapes()
