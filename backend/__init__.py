# backend/__init__.py
from .models import Base
from . import config, utils, models, geocode, versioning, log_utils

try:
    from . import parser
except ModuleNotFoundError:
    pass  # Only needed during live parsing, not for Alembic
