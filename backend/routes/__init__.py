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
from .media                import media_routes
from backend.routes import admin_geocode  # new import
from .admin_metrics        import admin_metrics_routes
from .jobs                 import jobs_routes
from .people_merge         import merge_routes

# ─── Meta endpoints ─────────────────────────────────────────────
from flask import Blueprint, jsonify
from backend.config import settings
meta_routes = Blueprint("meta", __name__, url_prefix="/api")

@meta_routes.route("/version", methods=["GET"])
def api_version():
    return jsonify({
        "app": "mapem-backend",
        "version": "2025.08.09",
        "db": str(getattr(settings, 'DB_HOST', 'unknown')),
        "port": settings.PORT,
    })

@meta_routes.route("/openapi.json", methods=["GET"])
def openapi_json():
    # Minimal hand-authored OpenAPI skeleton for discoverability
    return jsonify({
        "openapi": "3.0.0",
        "info": {"title": "MapEm API", "version": "2025.08.09"},
        "paths": {
            "/api/ping": {"get": {"summary": "Health check","responses": {"200": {}}}},
            "/api/people/{uploaded_tree_id}": {
                "get": {"summary": "List people","parameters": [{"name": "uploaded_tree_id","in":"path","required":True,"schema":{"type":"string","format":"uuid"}}]},
                "post": {"summary": "Create person"}
            },
            "/api/people/{uploaded_tree_id}/{person_id}": {
                "get": {"summary": "Get person"},
                "patch": {"summary": "Update person"},
                "delete": {"summary": "Delete person"}
            },
            "/api/people/{uploaded_tree_id}/export": {"get": {"summary": "Export people CSV"}},
            "/api/analytics/snapshot": {"get": {"summary": "System snapshot"}},
            "/api/analytics/surname-heatmap": {"get": {"summary": "Surname heatmap by era"}},
            "/api/analytics/cohort-flow": {"get": {"summary": "Sankey cohort flow"}},
            "/api/analytics/outliers": {"get": {"summary": "Outlier detection"}}
        }
    })

@meta_routes.route("/docs", methods=["GET"])
def docs_ui():
    # Lightweight Swagger UI via CDN using our OpenAPI JSON
    html = f"""
<!doctype html>
<html>
  <head>
    <meta charset='utf-8'>
    <title>MapEm API Docs</title>
    <link rel='stylesheet' href='https://unpkg.com/swagger-ui-dist@5/swagger-ui.css'>
  </head>
  <body>
    <div id='swagger-ui'></div>
    <script src='https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js' crossorigin></script>
    <script>
      window.ui = SwaggerUIBundle({
        url: '/api/openapi.json',
        dom_id: '#swagger-ui',
        presets: [SwaggerUIBundle.presets.apis],
        layout: 'BaseLayout',
      });
    </script>
  </body>
  </html>
"""
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


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
        admin_geocode.admin_geo,  # ✅ Manual fix route for unresolved
        admin_metrics_routes,
        jobs_routes,
        merge_routes,
        media_routes,
        meta_routes,

    ]

    for bp in routes:
        if bp.name in app.blueprints:
            logger.warning("⚠️  Skipping blueprint '%s' — already registered.", bp.name)
            continue
        app.register_blueprint(bp)
        logger.info("✅ Registered blueprint '%s' at prefix '%s'", bp.name, bp.url_prefix)
