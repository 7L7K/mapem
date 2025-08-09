from flask import Blueprint, jsonify, make_response, request
from sqlalchemy import func, extract, text
from sqlalchemy.exc import ProgrammingError

from backend.db import SessionLocal
from backend.models import Location, UploadedTree, Event, Individual
from backend.utils.helpers import haversine_km, phonetic_keys
from backend.models.enums import LocationStatusEnum
from backend.utils.logger import get_file_logger
from backend.utils.cache import ttl_cache_get, ttl_cache_set

log = get_file_logger("analytics")
analytics_routes = Blueprint("analytics", __name__, url_prefix="/api/analytics")

@analytics_routes.route("/snapshot", methods=["GET"])
def system_snapshot():
    cached = ttl_cache_get("analytics:snapshot")
    if cached is not None:
        resp = make_response(cached, 200)
        resp.headers["Cache-Control"] = "public, max-age=30"
        resp.headers["ETag"] = 'W/"analytics-snapshot"'
        return resp
    db    = SessionLocal()
    stats = {}
    try:
        # total
        stats["total_locations"] = db.query(func.count(Location.id)).scalar() or 0
        # by enum
        stats["resolved"]   = db.query(func.count(Location.id)).filter(Location.status == LocationStatusEnum.ok).scalar() or 0
        stats["unresolved"] = db.query(func.count(Location.id)).filter(Location.status == LocationStatusEnum.unresolved).scalar() or 0
        stats["manual"]     = db.query(func.count(Location.id)).filter(Location.status == LocationStatusEnum.manual_override).scalar() or 0
        stats["manual_fixes"] = stats["manual"]

        # safe “failed” count
        try:
            stats["failed"] = db.query(func.count(Location.id)).filter(Location.status == LocationStatusEnum.failed).scalar() or 0
        except (AttributeError, ProgrammingError):
            log.warning("`failed` not in enum/DB yet; skipping.")
            stats["failed"] = 0

        # timestamps
        lu = db.query(func.max(UploadedTree.created_at)).scalar()
        try:
            lm = db.query(func.max(Location.updated_at)).filter(Location.status == LocationStatusEnum.manual_override).scalar()
        except Exception:
            lm = None
        stats["last_upload"]      = lu.isoformat() if lu else None
        stats["last_manual_fix"]  = lm.isoformat() if lm else None

        # also include table counts for quick health
        row = db.execute(text("""
            SELECT
              (SELECT COUNT(*) FROM uploaded_trees)  AS uploaded_trees,
              (SELECT COUNT(*) FROM tree_versions)   AS tree_versions,
              (SELECT COUNT(*) FROM individuals)     AS individuals,
              (SELECT COUNT(*) FROM events)          AS events,
              (SELECT COUNT(*) FROM locations)       AS locations
        """)).fetchone()
        if row:
            stats.update(dict(row._mapping))
        payload = jsonify(stats)
        ttl_cache_set("analytics:snapshot", payload.get_json(), 30)
        resp = make_response(payload, 200)
        resp.headers["Cache-Control"] = "public, max-age=30"
        resp.headers["ETag"] = 'W/"analytics-snapshot"'
        return resp

    finally:
        db.close()


@analytics_routes.route("/surname-heatmap", methods=["GET"])
def surname_heatmap():
    """
    Aggregate counts by location for a given surname (or phonetic cluster) and optional year or era.
    Query params:
      - tree_id: UUID of tree_version (optional; if absent, aggregates across all trees)
      - surname: string (optional; if empty, returns overall counts)
      - era: e.g. 1850-1900 (inclusive) or preset: colonial, industrial, modern
      - year: specific year (takes precedence over era if provided)
      - phonetic: bool (default true) – cluster by Double Metaphone
    Response: { pins: [{location_name, count}], shapes: [] } (no shapes here; UI can reuse /api/heatmap)
    """
    db = SessionLocal()
    try:
        tree_id  = request.args.get("tree_id")
        surname  = (request.args.get("surname") or "").strip()
        year     = request.args.get("year", type=int)
        era_raw  = request.args.get("era")
        phonetic = request.args.get("phonetic", "true").lower() in {"1","true","yes"}

        yr_min = yr_max = None
        if year:
            yr_min = yr_max = year
        elif era_raw:
            presets = {
                "colonial": (1600, 1799),
                "industrial": (1800, 1914),
                "modern": (1915, 2025),
            }
            if era_raw in presets:
                yr_min, yr_max = presets[era_raw]
            else:
                try:
                    parts = [int(p) for p in str(era_raw).split("-")]
                    if len(parts) == 2:
                        yr_min, yr_max = min(parts), max(parts)
                except Exception:
                    pass

        q = db.query(Event, Location)\
              .join(Location, Event.location_id == Location.id)
        if tree_id:
            q = q.filter(Event.tree_id == tree_id)
        if yr_min is not None:
            q = q.filter(extract("year", Event.date) >= yr_min)
        if yr_max is not None:
            q = q.filter(extract("year", Event.date) <= yr_max)

        rows = q.all()

        target_keys = None
        if surname:
            pkey, skey = phonetic_keys(surname)
            target_keys = {pkey, skey}

        counts = {}
        for evt, loc in rows:
            if not loc:
                continue
            if surname:
                # check participants for surname match (exact or phonetic)
                matched = False
                for person in evt.participants:
                    last = person.last_name or ""
                    if not last:
                        continue
                    if phonetic:
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

            key = (loc.normalized_name or loc.raw_name or "").upper()
            if not key:
                continue
            counts[key] = counts.get(key, 0) + 1

        pins = [{"location_name": k, "count": v} for k, v in counts.items()]
        return jsonify({"pins": pins, "shapes": []}), 200
    finally:
        db.close()


@analytics_routes.route("/cohort-flow", methods=["GET"])
def cohort_flow():
    """
    Build Sankey-ready triplets birth_region → marriage_region → death_region for people in a year slice.
    Query params: tree_id, yearMin, yearMax, region_level (city|state|country; default: state)
    Response: { nodes: [...], links: [{source, target, value}] }
    """
    db = SessionLocal()
    try:
        tree_id = request.args.get("tree_id")
        yr_min = request.args.get("yearMin", type=int)
        yr_max = request.args.get("yearMax", type=int)
        level  = (request.args.get("region_level") or "state").lower()

        # Pull core events per person
        q = db.query(Event).filter(Event.event_type.in_(["birth","marriage","death"]))
        if tree_id:
            q = q.filter(Event.tree_id == tree_id)
        if yr_min is not None:
            q = q.filter(extract("year", Event.date) >= yr_min)
        if yr_max is not None:
            q = q.filter(extract("year", Event.date) <= yr_max)
        events = q.all()

        # group by person_id
        by_person = {}
        for e in events:
            if not e.participants:
                continue
            pid = e.participants[0].id  # primary participant heuristic
            person = by_person.setdefault(pid, {})
            person[e.event_type] = e

        def region(loc_name: str) -> str:
            if not loc_name:
                return "?"
            name = str(loc_name)
            parts = [p.strip() for p in name.replace("_", " ").split(",") if p.strip()]
            # naive: last token as state/country
            if level == "city":
                return parts[0] if parts else name
            if level == "country":
                return parts[-1] if parts else name
            # default state
            return parts[-2] if len(parts) >= 2 else (parts[-1] if parts else name)

        trip_counts = {}
        for pid, evs in by_person.items():
            b = evs.get("birth")
            m = evs.get("marriage")
            d = evs.get("death")
            if not (b and d):
                continue
            b_reg = region((b.location.normalized_name if b.location else None) or (b.location.raw_name if b.location else None))
            m_reg = region((m.location.normalized_name if (m and m.location) else None) or (m.location.raw_name if (m and m.location) else None)) if m else "(no marriage)"
            d_reg = region((d.location.normalized_name if d.location else None) or (d.location.raw_name if d.location else None))
            key = (b_reg, m_reg, d_reg)
            trip_counts[key] = trip_counts.get(key, 0) + 1

        # Build nodes/links for Sankey: birth→marriage and marriage→death
        node_index = {}
        nodes = []
        def get_idx(label: str) -> int:
            if label not in node_index:
                node_index[label] = len(nodes)
                nodes.append({"name": label})
            return node_index[label]

        links = {}
        for (b_reg, m_reg, d_reg), val in trip_counts.items():
            s1, t1 = get_idx(b_reg), get_idx(m_reg)
            s2, t2 = get_idx(m_reg), get_idx(d_reg)
            links[(s1, t1)] = links.get((s1, t1), 0) + val
            links[(s2, t2)] = links.get((s2, t2), 0) + val

        link_list = [{"source": s, "target": t, "value": v} for (s, t), v in links.items()]
        return jsonify({"nodes": nodes, "links": link_list}), 200
    finally:
        db.close()


@analytics_routes.route("/outliers", methods=["GET"])
def outliers():
    """
    Detect improbable moves (>1500km in <1 year) and age anomalies (>110 years).
    Query: tree_id, speed_km (default 1500), window_years (default 1), max_age (default 110)
    Returns: { moves: [...], ages: [...] }
    """
    db = SessionLocal()
    try:
        tree_id = request.args.get("tree_id")
        speed_km = request.args.get("speed_km", default=1500, type=int)
        window   = request.args.get("window_years", default=1, type=int)
        max_age  = request.args.get("max_age", default=110, type=int)

        # Fetch all events for birth/death + residences sorted by person/date
        q = db.query(Event).join(Individual, Event.participants).filter(Event.event_type.in_(["birth","death","residence","marriage"]))
        if tree_id:
            q = q.filter(Event.tree_id == tree_id)
        events = q.order_by(Event.date.asc()).all()

        # Build by person timeline
        by_person = {}
        for e in events:
            for p in e.participants:
                by_person.setdefault(p.id, []).append(e)

        # Age anomalies
        age_flags = []
        from datetime import date as _date
        for pid, evs in by_person.items():
            b = next((e for e in evs if e.event_type == "birth" and e.date), None)
            d = next((e for e in evs if e.event_type == "death" and e.date), None)
            if b and d and b.date and d.date:
                age = d.date.year - b.date.year - ((d.date.month, d.date.day) < (b.date.month, b.date.day))
                if age > max_age:
                    age_flags.append({
                        "person_id": str(pid),
                        "age": age,
                        "birth": b.date.isoformat(),
                        "death": d.date.isoformat(),
                    })

        # Improbable moves
        move_flags = []
        for pid, evs in by_person.items():
            evs.sort(key=lambda e: e.date or _date.min)
            for prev, curr in zip(evs, evs[1:]):
                lp, lc = prev.location, curr.location
                if not lp or not lc:
                    continue
                if not prev.date or not curr.date:
                    continue
                years = abs(curr.date.year - prev.date.year)
                if years <= window:
                    dist = haversine_km(lp.latitude, lp.longitude, lc.latitude, lc.longitude)
                    if dist >= speed_km:
                        move_flags.append({
                            "person_id": str(pid),
                            "from": {"name": lp.normalized_name or lp.raw_name, "lat": lp.latitude, "lng": lp.longitude},
                            "to":   {"name": lc.normalized_name or lc.raw_name, "lat": lc.latitude, "lng": lc.longitude},
                            "years": years,
                            "distance_km": round(dist, 1),
                            "event_types": [prev.event_type, curr.event_type],
                        })

        return jsonify({"moves": move_flags, "ages": age_flags}), 200
    finally:
        db.close()
