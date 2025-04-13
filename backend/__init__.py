# backend/__init__.py

# Only expose Base for Alembic or metadata usage
from backend.models import Base

# Don’t import heavy modules here — do it in the actual files that need them

# Optional: Lazy import parser only when needed
try:
    from backend.services import parser
except ModuleNotFoundError:
    pass  # Only needed during live parsing, not for Alembic
