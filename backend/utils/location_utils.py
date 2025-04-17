# backend/utils/location_utils.py
from typing import Optional
from backend.services.location_processor import normalize_location

def normalize_place(raw: Optional[str]) -> str:
    """
    Single function used everywhere for consistent normalization.
    Allows raw to be None, returning an empty string if so.
    """
    if not raw:
        return ""
    return normalize_location(raw)
