# os.path.expanduser("~")/mapem/backend/routes/upload.py
from flask import Blueprint, request, jsonify
import traceback, os
from backend.services.parser import GEDCOMParser
from backend.services.location_service import LocationService
from backend.utils.helpers import get_db_connection
from backend.models import TreeVersion, UploadedTree

upload_routes = Blueprint("upload", __name__, url_prefix="/api/upload")

@upload_routes.route("/", methods=["POST", "GET"], strict_slashes=False)
def upload_tree():
    session = get_db_connection()
    file = None
    tree_id = None
    temp_path = None

    try:
        # 1) Validate incoming request
        file = request.files.get('gedcom_file')
        filename = file.filename or ""
        if not file or filename.strip() == "":
            return jsonify({"error": "Missing file"}), 400

        tree_name = request.form.get("tree_name")
        uploader = request.form.get("uploader_name", "Anonymous")
        if not tree_name:
            return jsonify({"error": "Missing tree_name"}), 400

        # 2) Save GEDCOM file to temp path
        temp_path = f"/tmp/{file.filename}"
        file.save(temp_path)

        # 3) Instantiate LocationService + pass to GEDCOMParser
        from backend.services.location_service import LocationService
        api_key = os.getenv("GOOGLE_MAPS_API_KEY", "YOUR_FALLBACK_KEY")
        location_service = LocationService(api_key=api_key)
        
        parser = GEDCOMParser(temp_path, location_service)
        parser.parse_file()  # parse individuals/families/events

        # 4) Insert UploadedTree row
        try:
            uploaded_tree = UploadedTree(
                original_filename=file.filename,
                uploader_name=uploader
            )
            session.add(uploaded_tree)
            session.flush()
            tree_id = uploaded_tree.id
        except Exception as ex:
            session.rollback()
            return jsonify({"error": "Failed to save UploadedTree", "details": str(ex)}), 500

        # 5) Insert TreeVersion row
        try:
            version = TreeVersion(
                tree_name=tree_name,
                version_number=1,
                uploaded_tree_id=tree_id
            )
            session.add(version)
            session.flush()
        except Exception as ex:
            session.rollback()
            return jsonify({"error": "Failed to save TreeVersion", "details": str(ex)}), 500

        # 6) Save GEDCOM data to DB
        try:
            # No geocode_client needed; parser uses location_service
            result = parser.save_to_db(session, tree_id=tree_id, dry_run=False)
            print("✅ Upload Summary:", result)
        except Exception as ex:
            session.rollback()
            return jsonify({
                "error": "Failed during GEDCOM DB insert",
                "details": str(ex),
                "trace": traceback.format_exc()
            }), 500

        # 7) Commit everything
        session.commit()

        return jsonify({
            "status": "success",
            "uploaded_tree_id": tree_id,
            "version_id": version.id,
            "summary": result
        }), 200

    except Exception as e:
        session.rollback()
        print("🚨 Top-level upload failure:", e)
        print("🚨 FULL TRACEBACK START 🚨")
        print(traceback.format_exc())
        print("🚨 FULL TRACEBACK END 🚨")
        return jsonify({
            "error": "Top-level upload failure",
            "details": str(e),
            "trace": traceback.format_exc()
        }), 500

    finally:
        if session:
            session.close()
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
