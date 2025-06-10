# ✅ backend/services/geocode/__init__.py
from .geocode import Geocode, GEOCODER

def get_geocoder():
    return GEOCODER

__all__ = ["Geocode", "GEOCODER", "get_geocoder"]
