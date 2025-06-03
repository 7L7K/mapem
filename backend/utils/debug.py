import functools, logging, json

log = logging.getLogger("mapem")

def trace(msg):
    """
    Usage:
    @trace("tree_counts")
    def tree_counts(...):
        ...
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kw):
            log.debug(f"[{msg}] ➡️ args={args} kw={kw}")
            res = fn(*args, **kw)
            safe = res
            try:
                safe = json.dumps(res)[:400]  # truncate big payloads
            except Exception:
                pass
            log.debug(f"[{msg}] ⬅️ {safe}")
            return res
        return wrapper
    return decorator
