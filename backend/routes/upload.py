# os.path.expanduser("~")/mapem/backend/routes/upload.py

from flask import Blueprint, request, jsonify
import traceback, os

from backend.services.parser import GEDCOMParser
from backend.services.location_service import LocationService
from backend.utils.helpers import generate_temp_path  # if you got one
from backend.models import TreeVersion, UploadedTree
from backend.db import get_db
import logging

upload_routes = Blueprint("upload", __name__, url_prefix="/api/upload")
logger = logging.getLogger("mapem")

@upload_routes.route("/", methods=["POST", "GET"], strict_slashes=False)
def upload_tree():
    db = next(get_db())  # 🔁 use new session pattern
    temp_path = None

    try:
        # 1) Validate incoming request
        file = request.files.get('gedcom_file')
        if not file or not file.filename.strip():
            return jsonify({"error": "Missing file"}), 400

        tree_name = request.form.get("tree_name")
        uploader = request.form.get("uploader_name", "Anonymous")
        if not tree_name:
            return jsonify({"error": "Missing tree_name"}), 400

        # 2) Save GEDCOM file to temp path
        temp_path = f"/tmp/{file.filename}"
        file.save(temp_path)

        # 3) Set up location service
        api_key = os.getenv("GOOGLE_MAPS_API_KEY", "YOUR_FALLBACK_KEY")
        location_service = LocationService(api_key=api_key)
        parser = GEDCOMParser(temp_path, location_service)
        parser.parse_file()

        # 4) Save UploadedTree + TreeVersion
        uploaded_tree = UploadedTree(
            original_filename=file.filename,
            uploader_name=uploader
        )
        db.add(uploaded_tree)
        db.flush()  # get ID
        tree_id = uploaded_tree.id

        version = TreeVersion(
            tree_name=tree_name,
            version_number=1,
            uploaded_tree_id=tree_id
        )
        db.add(version)
        db.flush()

        # 5) Save parsed GEDCOM to DB
        result = parser.save_to_db(db, tree_id=tree_id, dry_run=False)

        # 6) Commit transaction
        db.commit()

        return jsonify({
            "status": "success",
            "uploaded_tree_id": tree_id,
            "version_id": version.id,
            "summary": result
        }), 200

    except Exception as e:
        db.rollback()
        logger.exception("❌ Upload failed")
        return jsonify({
            "error": "Upload failed",
            "details": str(e),
            "trace": traceback.format_exc()
        }), 500

    finally:
        db.close()
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
