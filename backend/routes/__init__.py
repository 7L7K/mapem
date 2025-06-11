"""
Central blueprint registry.
Adds new routes safely (skips if already registered) and logs everything.
"""

from backend.utils.logger import get_file_logger
logger = get_file_logger("route_registry")

# ─── Modular Routes ─────────────────────────────────────────────
from .upload               import upload_routes
from .trees                import tree_routes
from .events               import event_routes
from .people               import people_routes
from .timeline             import timeline_routes
from .schema               import schema_routes
from .debug                import debug_routes
from .movements            import movements_routes
from .health               import health_routes
from .heatmap              import heatmap_routes
from .geocode_api          import bp as geocode_routes   # 🆕 Admin API
from .geocode_dashboard    import geocode_dashboard      # 🆕 UI pages
from .analytics            import analytics_routes

from backend.utils.debug_routes import debug_route

# ─── Register All Blueprints Safely ─────────────────────────────
@debug_route
def register_routes(app):
    """Call this once in main.py to wire every route blueprint."""

    routes = [
        upload_routes,
        tree_routes,
        event_routes,
        people_routes,
        timeline_routes,
        schema_routes,
        debug_routes,
        movements_routes,
        health_routes,
        heatmap_routes,
        analytics_routes,
        geocode_routes,        # 🧭 Admin geocode API endpoints
        geocode_dashboard,     # 📊 Geocode dashboard views
    ]

    for bp in routes:
        if bp.name in app.blueprints:
            logger.warning("⚠️  Skipping blueprint '%s' — already registered.", bp.name)
            continue
        app.register_blueprint(bp)
        logger.info("✅ Registered blueprint '%s' at prefix '%s'", bp.name, bp.url_prefix)
