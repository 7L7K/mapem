import os
import json
import traceback
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import func

from backend.db import get_db_connection
from backend.models import Event, Location, Individual

heatmap_routes = Blueprint("heatmap", __name__, url_prefix="/api/heatmap")

# Caches for GeoJSON shapes
SHAPES_INDEX = {}
SHAPES_LOADED = False

def load_shapes():
    """Load all .geojson files under historical_places/ into SHAPES_INDEX."""
    global SHAPES_LOADED, SHAPES_INDEX
    if SHAPES_LOADED:
        return
    SHAPES_INDEX = {}
    shapes_dir = os.path.join(os.path.dirname(__file__), "..", "historical_places")
    current_app.logger.debug(f"Looking for shapes in {shapes_dir}")
    if os.path.isdir(shapes_dir):
        for fname in os.listdir(shapes_dir):
            if not fname.lower().endswith(".geojson"):
                continue
            path = os.path.join(shapes_dir, fname)
            try:
                with open(path) as f:
                    data = json.load(f)
                    for feature in data.get("features", []):
                        props = feature.get("properties", {})
                        name = props.get("normalized_name") or props.get("name")
                        if name:
                            SHAPES_INDEX[name.upper()] = feature
                current_app.logger.debug(f"Loaded shapes from {fname}")
            except Exception as e:
                current_app.logger.error(f"Error loading shape {path}: {e}")
    else:
        current_app.logger.debug("No historical_places directory found, skipping shapes")
    SHAPES_LOADED = True
    current_app.logger.debug(f"Total shapes indexed: {len(SHAPES_INDEX)}")

def extract_surname(full_name: str) -> str:
    """Basic surname extraction: last word, uppercased."""
    try:
        if not full_name or not isinstance(full_name, str):
            return ""
        name = full_name.replace('"', "").strip()
        parts = name.split()
        return parts[-1].upper() if parts else ""
    except Exception as e:
        current_app.logger.error(f"Surname parse error for '{full_name}': {e}")
        return ""

@heatmap_routes.route("/", methods=["GET"], strict_slashes=False)
def get_heatmap():
    """Return both pin clusters and optional GeoJSON shapes for a given year + tree(s)."""
    try:
        # Params
        tree_ids = request.args.get("tree_ids", "")
        year = request.args.get("year", "")
        surname = request.args.get("surname", "").upper()
        current_app.logger.debug(f"Heatmap params: tree_ids={tree_ids}, year={year}, surname={surname}")

        # Validate
        if not tree_ids or not year:
            return jsonify({"error": "tree_ids and year are required"}), 400
        t_ids = [int(x) for x in tree_ids.split(",") if x.isdigit()]
        y = int(year)

        session = get_db_connection()
        # Base query: join Event → Location
        query = session.query(Event, Location).join(Location, Event.location_id == Location.id)
        query = query.filter(Event.tree_id.in_(t_ids))
        query = query.filter(Event.date >= datetime(y, 1, 1), Event.date <= datetime(y, 12, 31))

        # Surname filter
        if surname:
            query = query.join(Individual, Event.individual_id == Individual.id)
            query = query.filter(extract_surname(Individual.name) == surname)

        raw = query.all()
        current_app.logger.debug(f"Raw records fetched: {len(raw)}")

        # Dedupe per person+location
        heat = {}
        for evt, loc in raw:
            #if loc.latitude is None or loc.longitude is None:
                #current_app.logger.debug(f"Skipping loc {loc.id} missing coords")
                #continue
            key = loc.id
            if key not in heat:
                heat[key] = {
                    "location_id": loc.id,
                    "location_name": loc.name,
                    "lat": loc.latitude,
                    "lng": loc.longitude,
                    "count": 0,
                    "tree_counts": {},
                    "_seen": set()
                }
            entry = heat[key]
            person_loc = (evt.individual_id, loc.id)
            if person_loc in entry["_seen"]:
                continue
            entry["_seen"].add(person_loc)
            entry["count"] += 1
            tid = str(evt.tree_id)
            entry["tree_counts"][tid] = entry["tree_counts"].get(tid, 0) + 1

        # Build pins list
        pins = []
        for e in heat.values():
            e.pop("_seen", None)
            pins.append(e)

        # Build shapes list (if any)
        shapes = []
        for pin in pins:
            name_key = pin["location_name"].upper()
            feature = SHAPES_INDEX.get(name_key)
            if feature:
                f = feature.copy()
                f["properties"]["count"] = pin["count"]
                f["properties"]["tree_counts"] = pin["tree_counts"]
                shapes.append(f)

        return jsonify({"pins": pins, "shapes": shapes}), 200

    except Exception as e:
        tb = traceback.format_exc()
        current_app.logger.error(f"get_heatmap error: {e}\n{tb}")
        return jsonify({"error": str(e), "trace": tb}), 500
    finally:
        try: session.close()
        except: pass

@heatmap_routes.route("/events", methods=["GET"], strict_slashes=False)
def get_heatmap_events():
    """Drilldown: list distinct individuals for a given location, year & tree."""
    try:
        loc_id = request.args.get("location_id")
        year = request.args.get("year")
        tree_id = request.args.get("tree_id")
        current_app.logger.debug(f"Drill params: loc={loc_id}, year={year}, tree={tree_id}")

        # Validate
        if not loc_id or not year or not tree_id:
            return jsonify({"error": "location_id, year, and tree_id required"}), 400
        lid, y, tid = int(loc_id), int(year), int(tree_id)

        session = get_db_connection()
        q = (session.query(Event, Individual, Location)
             .join(Individual, Event.individual_id == Individual.id)
             .join(Location, Event.location_id == Location.id)
             .filter(Event.location_id == lid,
                     Event.tree_id == tid,
                     Event.date >= datetime(y, 1, 1),
                     Event.date <= datetime(y, 12, 31)))
        rows = q.all()
        current_app.logger.debug(f"Drill rows fetched: {len(rows)}")

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
        try: session.close()
        except: pass
        
def warmup_heatmap():
    load_shapes()

