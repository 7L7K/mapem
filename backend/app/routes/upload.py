#/Users/kingal/mapem/backend/app/routes/upload.py
from flask import Blueprint, request, jsonify
import traceback, threading
from app.services.parser import GEDCOMParser
from app.services.geocode import Geocode
from app.utils.helpers import get_db_connection
from app.models import UploadedTree
#from app.services import geocode
import os

upload_routes = Blueprint("upload", __name__)

@upload_routes.route("/upload_tree", methods=["POST"])
def upload_tree():
    try:
        file = request.files.get('gedcom_file')
        if not file or file.filename == '':
            return jsonify({"error": "Missing file"}), 400

        tree_name = request.form.get("tree_name")
        uploader = request.form.get("uploader_name", "Anonymous")
        if not tree_name:
            return jsonify({"error": "Missing tree_name"}), 400

        temp_path = f"/tmp/{file.filename}"
        file.save(temp_path)

        parser = GEDCOMParser(temp_path)
        parser.parse_file()
        session = get_db_connection()

        tree = UploadedTree(original_filename=file.filename, uploader_name=uploader)
        session.add(tree)
        session.flush()
        tree_id = tree.id

        result = parser.save_to_db(session, tree_id=tree_id)
        session.commit()
        session.close()

#        threading.Thread(
#            target=lambda: geocode_missing_fast(batch_size=100, max_workers=5),
#            daemon=True
#        ).start()

        return jsonify({"status": "success", "tree_id": tree_id, "summary": result})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500
