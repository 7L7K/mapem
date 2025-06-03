import logging
from uuid import UUID
from flask import jsonify

log = logging.getLogger("mapem")

def parse_uuid_arg(name: str, raw: str):
    try:
        return UUID(raw)
    except Exception:
        log.warning(f"⚠️ Invalid UUID for {name}: {raw}")
        raise ValueError(f"{name} must be a valid UUID")

def parse_uuid_arg_or_400(name: str, raw: str):
    try:
        return UUID(raw)
    except Exception:
        log.warning(f"⚠️ Invalid UUID for {name}: {raw}")
        return jsonify({"error": f"{name} must be a valid UUID", "code": "invalid_uuid"}), 400

if __name__ == "__main__":
    log.info("▶️ parse_uuid_arg: %s", parse_uuid_arg("tree_id", "6fa459ea-ee8a-3ca4-894e-db77e160355e"))
    try:
        parse_uuid_arg("tree_id", "not-a-uuid")
    except ValueError as e:
        log.info("❌ parse_uuid_arg failed as expected: %s", e)
