from flask import Blueprint, jsonify
from sqlalchemy import inspect
from backend.db import get_engine
from backend.utils.uuid_utils import parse_uuid_arg_or_400
from backend.utils.debug_routes import debug_route

schema_routes = Blueprint("schema", __name__, url_prefix="/api/schema")

@schema_routes.route("/", methods=["GET"])
@debug_route
def get_schema():
    try:
        insp = inspect(get_engine())
        schema = {tbl: [
            {"name": c["name"], "type": str(c["type"]),
             "nullable": c["nullable"], "default": c["default"]}
            for c in insp.get_columns(tbl)]
            for tbl in insp.get_table_names()}
        return jsonify(schema)
    except Exception as e:
        import traceback, json
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

@schema_routes.route("/<string:tree_id>", methods=["GET"])
@debug_route
def get_schema_with_tree_id(tree_id: str):
    """Stub route now UUID-safe."""
    parsed = parse_uuid_arg_or_400("tree_id", tree_id)
    if isinstance(parsed, tuple):
        return parsed
    return get_schema()
