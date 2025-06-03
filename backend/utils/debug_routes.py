# backend/utils/debug_routes.py

import traceback
import logging
from functools import wraps
from flask import request, has_request_context, jsonify

log = logging.getLogger("mapem")

def debug_route(fn):
    """
    Wraps route functions. Only touches request object if inside a real request context.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if has_request_context():
            log.debug(f"→ ENTER {request.method} {request.path}")
            log.debug(f"   Query args: {dict(request.args)}")
            log.debug(f"   Body: {request.get_json(silent=True)}")
        else:
            log.debug(f"→ ENTER {fn.__name__} (no request context)")

        try:
            response = fn(*args, **kwargs)
            return response
        except Exception as e:
            tb = traceback.format_exc()
            log.error(f"‼ ERROR in {fn.__name__}: {e}\n{tb}")
            return jsonify({"error": str(e), "trace": tb.splitlines()}), 500

    return wrapper
