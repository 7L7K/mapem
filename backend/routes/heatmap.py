# backend/routes/heatmap.py

import os
import json
import traceback
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import func

from backend.db import get_db
from backend.models import Event, Location, Individual
from backend.utils.helpers import phonetic_keys
from backend.utils.debug_routes import debug_route
from backend.utils.redaction import is_authorized

heatmap_routes = Blueprint("heatmap", __name__, url_prefix="/api/heatmap")

# Caches for GeoJSON shapes
SHAPES_INDEX = {}
SHAPES_LOADED = False

def _shapes_base_dir() -> Path:
    return Path(__file__).resolve().parent / ".." / "data" / "historical_places"

@debug_route
def load_shapes():
    """Load all .geojson files under historical_places/ into SHAPES_INDEX."""
    global SHAPES_LOADED, SHAPES_INDEX
    if SHAPES_LOADED:
        return
    base = _shapes_base_dir()
    for root, _, files in os.walk(str(base)):
        for fn in files:
            if fn.lower().endswith((".geojson", ".json")):
                path = os.path.join(root, fn)
                try:
                    feat = json.load(open(path))
                    # Accept either Feature or dict name→props
                    if feat.get("type") == "Feature":
                        key = feat.get("properties", {}).get("name", fn).upper()
                        SHAPES_INDEX[key] = feat
                    elif isinstance(feat, dict):
                        for k, v in feat.items():
                            SHAPES_INDEX[str(k).upper()] = {
                                "type": "Feature",
                                "properties": {"name": k, **(v if isinstance(v, dict) else {})},
                                "geometry": None,
                            }
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
        authorized = is_authorized(request.headers)
        tree_ids = request.args.get("tree_ids", "")
        year = request.args.get("year", "")
        surname = (request.args.get("surname", "") or "").strip()
        use_phonetic = request.args.get("phonetic", "true").lower() in {"1","true","yes"}

        # Fetch raw counts per location
        heat = {}
        q = db.query(Event, Location).join(Location, Event.location_id == Location.id)
        if tree_ids:
            ids = [x.strip() for x in tree_ids.split(",") if x.strip()]
            q = q.filter(Event.tree_id.in_(ids))
        if year:
            q = q.filter(func.extract("year", Event.date) == int(year))
        rows = q.all()

        target_keys = None
        if surname:
            p, s = phonetic_keys(surname)
            target_keys = {p, s}

        for evt, loc in rows:
            name = (loc.normalized_name or loc.raw_name or "").upper()
            if surname:
                # Check participants by surname (phonetic by default)
                matched = False
                for p in evt.participants:
                    last = (p.last_name or "").strip()
                    if not last:
                        continue
                    if use_phonetic:
                        k1, k2 = phonetic_keys(last)
                        if target_keys & {k1, k2}:
                            matched = True
                            break
                    else:
                        if last.lower() == surname.lower():
                            matched = True
                            break
                if not matched:
                    continue
            entry = heat.setdefault(name, {
                "location_name": loc.normalized_name or loc.raw_name,
                "count": 0,
                "tree_counts": {}
            })
            entry["count"] += 1
            entry["tree_counts"][evt.tree_id] = entry["tree_counts"].get(evt.tree_id, 0) + 1

        # Build pins list
        pins = []
        pins.extend(heat.values())

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
                # Optional: if requesting a specific year, expose it for frontend styling
                if year:
                    fcopy["properties"]["year"] = int(year)
                # If unauthorized viewers, strip any sensitive props (none expected here, but future-proof)
                if not authorized:
                    # keep only whitelisted props
                    props = fcopy.get("properties", {})
                    fcopy["properties"] = {
                        "name": props.get("name"),
                        "count": props.get("count"),
                        "tree_counts": props.get("tree_counts"),
                        "year": props.get("year"),
                    }
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
