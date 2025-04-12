from flask import Blueprint, jsonify
from sqlalchemy import inspect
from app.utils.helpers import get_engine

schema_routes = Blueprint("schema", __name__, url_prefix="/api/schema")

@schema_routes.route("/", methods=["GET"])
def get_schema():
    try:
        insp = inspect(get_engine())
        schema = {}
        for table_name in insp.get_table_names():
            schema[table_name] = [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                    "default": col["default"]
                } for col in insp.get_columns(table_name)
            ]
        return jsonify(schema)
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500
