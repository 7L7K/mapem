"""Simple in-memory TTL cache for lightweight route responses.

Not for cross-process use. Safe for single-process dev/test.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Tuple

_STORE: Dict[str, Tuple[float, Any]] = {}


def ttl_cache_get(key: str) -> Any | None:
    now = time.time()
    item = _STORE.get(key)
    if not item:
        return None
    expires_at, value = item
    if now >= expires_at:
        _STORE.pop(key, None)
        return None
    return value


def ttl_cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    _STORE[key] = (time.time() + max(0, int(ttl_seconds)), value)


