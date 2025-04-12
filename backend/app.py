#!/usr/bin/env python
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os, tempfile, shutil, logging
import traceback  # make sure this is at the top
from sqlalchemy import inspect  # ✅ add this import at the top
from sqlalchemy.sql import func  # ✅ Add this with your other sqlalchemy imports'from flask_cors import CORS

from sqlalchemy.orm import joinedload
from flask import jsonify
from flask import Flask, request, jsonify
from backend.parser import GEDCOMParser
from backend.geocode import Geocode
from backend.utils import get_db_connection
from backend.models import UploadedTree
from sqlalchemy.orm import Session


from backend import config, utils, models, log_utils, versioning, geocode, parser
from backend.geocode import Geocode
from backend.utils import get_db_connection
from dotenv import load_dotenv


load_dotenv()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("app")

app = Flask(__name__)

CORS(app, supports_credentials=True, origins=[
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173"   # Some browsers resolve localhost as 127.0.0.1
])


app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['TRAP_HTTP_EXCEPTIONS'] = True
app.config.from_object(config)

# FULL‑COVERAGE CORS (dev only – in prod lock it down)


engine = create_engine(config.DATABASE_URI)
models.Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

geocode_client = geocode.Geocode(config.GOOGLE_MAPS_API_KEY)

@app.route("/upload_tree", methods=["POST"])
def upload_tree():
    try:
        # 🔐 Check file
        if 'gedcom_file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['gedcom_file']
        if file.filename == '':
            return jsonify({"error": "Empty filename"}), 400

        # 🔐 Required metadata
        tree_name = request.form.get("tree_name")
        uploader = request.form.get("uploader_name", "Anonymous")

        if not tree_name:
            return jsonify({"error": "Missing tree_name"}), 400

        print(f"🌳 Received tree: {tree_name} from {uploader}")

        # Save file temporarily
        temp_path = f"/tmp/{file.filename}"
        file.save(temp_path)

        # Parse + Insert
        parser = GEDCOMParser(temp_path)
        parser.parse_file()
        session = get_db_connection()

        # Upload record
        tree = UploadedTree(
            original_filename=file.filename,
            uploader_name=uploader,
            notes=""
        )
        session.add(tree)
        session.flush()

        tree_id = tree.id  # ✅ Capture ID before session closes

        # Save full tree
        result = parser.save_to_db(session, tree_id=tree_id, geocode_client=geocode_client, dry_run=False)

        session.commit()
        session.close()

        print(f"✅ Upload complete: {result}")
        return jsonify({
            "status": "success",
            "tree_id": tree_id,
            "summary": result
        })

    except Exception as e:
        import traceback
        print("🔥 Upload failed:", str(e))
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "trace": traceback.format_exc()
        }), 500



@app.route('/tree/<int:tree_id>', methods=['GET'])
def get_tree_version(tree_id):
    session = Session()
    try:
        tree = session.query(models.TreeVersion).filter_by(id=tree_id).first()
        if not tree:
            return jsonify({"error": "Tree not found"}), 404
        return jsonify({
            "tree_name": tree.tree_name,
            "version": tree.version_number,
            "created_at": tree.created_at.isoformat(),
            "diff_summary": tree.diff_summary
        }), 200
    finally:
        session.close()

@app.route("/api/movements/<int:tree_id>")
def get_movements(tree_id):
    session = get_db_connection()
    try:
        print(f"📡 Fetching movements for tree_id: {tree_id}")
        migration_events = (
            session.query(models.Event)
            .options(joinedload(models.Event.individual), joinedload(models.Event.location))
            .filter(
                models.Event.tree_id == tree_id,
                models.Event.location_id.isnot(None)
            )
            .all()
        )
        print(f"📦 Found {len(migration_events)} events with location")

        result = []
        skipped = 0
        for event in migration_events:
            if not event.location or not event.location.lat or not event.location.lng:
                skipped += 1
                continue

            result.append({
                "name": event.individual.name if event.individual else "Unknown",
                "event_type": event.event_type,
                "year": event.date.year if event.date else None,
                "location": event.location.raw_name,
                "lat": float(event.location.lat),
                "lng": float(event.location.lng),
            })

        print(f"✅ Returning {len(result)} valid events (skipped {skipped})")
        return jsonify(result)

    except Exception as e:
        logger.error(f"❌ Failed to fetch movements: {e}")
        return jsonify([]), 500
    finally:
        session.close()

@app.route("/api/tree/<int:tree_id>")
def get_tree_structure(tree_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, full_name
        FROM tree_people
        WHERE tree_id = %s
    """, (tree_id,))
    people = cur.fetchall()
    print(f"👥 People for tree {tree_id}: {people}")
    cur.execute("""
        SELECT person_id, related_person_id, relationship_type
        FROM tree_relationships
        WHERE tree_id = %s
    """, (tree_id,))
    relationships = cur.fetchall()
    print(f"🔗 Relationships for tree {tree_id}: {relationships}")
    cur.close()
    conn.close()
    nodes = [{"data": {"id": str(p[0]), "label": p[1]}} for p in people]
    edges = [{"data": {"source": str(r[0]), "target": str(r[1]), "label": r[2]}} for r in relationships]
    return jsonify({"nodes": nodes, "edges": edges})

@app.route("/")
def index():
    return jsonify({"message": "API is live"}), 200

@app.route("/debug-cors", methods=["GET", "OPTIONS"])
def debug_cors():
    return jsonify({"message": "CORS is working!"}), 200

# --- People list -----------------------------------------------------------
@app.route("/api/people", methods=["GET"])
def api_people():
    """
    Return up to 500 individuals across all trees (or filter by ?tree_id=).
    """
    limit = int(request.args.get("limit", 500))
    tree_id_raw = request.args.get("tree_id")
    tree_id = int(tree_id_raw) if tree_id_raw else None


    session = Session()
    try:
        q = session.query(models.Individual).order_by(models.Individual.id)
        if tree_id:
            q = q.filter(models.Individual.tree_id == tree_id)

        people = q.limit(limit).all()
        payload = [p.to_dict() for p in people]
        return jsonify(payload), 200
    finally:
        session.close()


@app.route("/api/events", methods=["GET"])
def get_events():
    from datetime import datetime
    tree_id_raw = request.args.get("tree_id")
    tree_id = int(tree_id_raw) if tree_id_raw else None
    category = request.args.get("category")
    person_id = request.args.get("person_id")
    start_year = request.args.get("start_year")
    end_year = request.args.get("end_year")
    
    session = Session()
    try:
        query = session.query(models.Event)
        if tree_id:
            query = query.filter(models.Event.tree_id == tree_id)
            print(f"🔎 Filter: tree_id == {tree_id}")
        if category:
            query = query.filter(models.Event.category == category)
            print(f"🔎 Filter: category == {category}")
        if person_id:
            query = query.filter(models.Event.individual_id == int(person_id))
            print(f"🔎 Filter: individual_id == {person_id}")
        if start_year:
            start = datetime(int(start_year), 1, 1)
            query = query.filter(models.Event.date != None, models.Event.date >= start)
            print(f"🔎 Filter: date >= {start_year}")
        if end_year:
            end = datetime(int(end_year), 12, 31)
            query = query.filter(models.Event.date != None, models.Event.date <= end)
            print(f"🔎 Filter: date <= {end_year}")
            
        events = query.all()
        print(f"🎯 Final event count after filters: {len(events)}")
        results = []
        for evt in events:
            try:
                event_dict = {
                    "id": evt.id,
                    "event_type": evt.event_type,
                    "date": evt.date.isoformat() if evt.date else None,
                    "date_precision": evt.date_precision,
                    "notes": evt.notes,
                    "source_tag": evt.source_tag,
                    "category": evt.category
                }
                if evt.individual:
                    event_dict["individual"] = {"id": evt.individual.id, "name": evt.individual.name}
                else:
                    print(f"⚠️ No individual linked to event {evt.id}")
                if evt.location:
                    event_dict["location"] = {
                        "name": evt.location.name,
                        "normalized_name": evt.location.normalized_name,
                        "latitude": evt.location.latitude,
                        "longitude": evt.location.longitude,
                        "confidence": evt.location.confidence_score
                    }
                else:
                    print(f"⚠️ No location linked to event {evt.id}")
                results.append(event_dict)
            except Exception as e:
                print(f"🔥 Error processing event {evt.id}")
                import traceback
                print(traceback.format_exc())
        return jsonify(results), 200
    except Exception as e:
        session.rollback()
        import traceback
        trace = traceback.format_exc()
        print("🔥 UNCAUGHT ERROR in /api/events")
        print(trace)
        return jsonify({"error": str(e), "trace": trace}), 500
    finally:
        session.close()


@app.before_request
def log_request_info():
    logger.debug(f"➡️ {request.method} {request.path}")
    logger.debug(f"🔍 Headers: {dict(request.headers)}")
    logger.debug(f"🧠 Body: {request.get_data()}")

@app.route("/api/timeline/<int:tree_id>", methods=["GET"])
def get_timeline(tree_id):
    session = Session()
    try:
        query = session.query(models.Event).filter(models.Event.tree_id == tree_id)
        events = query.all()

        timeline = []
        for evt in events:
            if evt.date:
                year = evt.date.year
                label = f"{evt.event_type.title()}"
                if evt.individual:
                    label += f" – {evt.individual.name}"
                timeline.append({
                    "year": str(year),
                    "event": label
                })

        timeline.sort(key=lambda x: x["year"])
        return jsonify(timeline), 200

    except Exception as e:
        session.rollback()
        logger.error("🔥 Timeline error:\n%s", traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.errorhandler(Exception)
def handle_all_errors(e):
    trace = traceback.format_exc()
    logger.error(f"🔥 Unhandled Exception:\n{trace}")
    print(trace)  # 👈 forces it to show up in your terminal
    response = jsonify({
        "error": str(e),
        "trace": trace
    })
    response.status_code = 500
    # 👇 Force CORS headers even on error
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response

@app.route("/trigger-error")
def trigger_error():
    raise RuntimeError("🔥 Forced error for debug tracing")

@app.route("/api/schema", methods=["GET"])
def get_schema():
    try:
        insp = inspect(engine)  # ✅ THIS is the correct way

        schema = {}
        for table_name in insp.get_table_names():
            columns = []
            for col in insp.get_columns(table_name):
                columns.append({
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                    "default": col["default"]
                })
            schema[table_name] = columns

        return jsonify(schema), 200

    except Exception as e:
        trace = traceback.format_exc()
        logger.error(f"❌ Error in /api/schema:\n{trace}")
        print(trace)
        return jsonify({"error": str(e), "trace": trace}), 500
    
@app.route("/api/trees", methods=["GET"])
def list_trees():
    session = Session()
    try:
        from sqlalchemy import func  # 💡 make sure this is up top too

        # Grab the latest version of each unique tree_name
        subquery = session.query(
            models.TreeVersion.tree_name,
            func.max(models.TreeVersion.id).label("max_id")
        ).group_by(models.TreeVersion.tree_name).subquery()

        latest_versions = session.query(models.TreeVersion).join(
            subquery, models.TreeVersion.id == subquery.c.max_id
        ).order_by(models.TreeVersion.created_at.desc()).all()

        tree_list = [{"id": t.id, "name": t.tree_name} for t in latest_versions]
        return jsonify(tree_list), 200

    except Exception as e:
        import traceback
        print("🔥 /api/trees failed")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route("/api/movements/<int:tree_id>", methods=["GET"])
def get_migration_events(tree_id):
    session = Session()
    try:
        migration_categories = ["migration"]
        events = session.query(models.Event).filter(
            models.Event.tree_id == tree_id,
            models.Event.category.in_(migration_categories)
        ).all()

        results = []
        for evt in events:
            if not evt.location or not evt.date:
                continue
            results.append({
                "id": evt.id,
                "event_type": evt.event_type,
                "date": evt.date.isoformat(),
                "individual_name": evt.individual.name if evt.individual else None,
                "location": {
                    "lat": evt.location.latitude,
                    "lng": evt.location.longitude,
                    "normalized_name": evt.location.normalized_name,
                    "confidence": evt.location.confidence_score
                }
            })

        print(f"🌍 Found {len(results)} migration events for tree {tree_id}")
        return jsonify(results), 200

    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        print(f"🔥 Error in /api/movements/{tree_id}")
        print(trace)
        return jsonify({"error": str(e), "trace": trace}), 500

    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True)
