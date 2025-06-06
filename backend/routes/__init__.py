#os.path.expanduser("~")/mapem/backend/routes/__init__.py
from .upload import upload_routes
from .trees import tree_routes
from .events import event_routes
from .people import people_routes
from .timeline import timeline_routes
from .schema import schema_routes
from .debug import debug_routes
from backend.routes.movements import movements_routes
from backend.routes.health import health_routes
from backend.routes.heatmap import heatmap_routes
from backend.utils.debug_routes import debug_route
import logging

 




@debug_route
def register_routes(app):
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
        

    ]

    for bp in routes:
        if bp.name in app.blueprints:
            logger.warning("⚠️ Skipping blueprint '%s' — already registered.", bp.name)
            continue
        app.register_blueprint(bp)
