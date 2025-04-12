# backend/__init__.py
from app.models import Base
from backend import config, utils, geocode, versioning, log_utils

try:
    from app.services import parser  # ✅ Clean import
except ModuleNotFoundError:
    pass  # Only needed during live parsing, not for Alembic
