from .upload import upload_routes
from .trees import tree_routes
from .events import event_routes
from .people import people_routes
from .timeline import timeline_routes
from .schema import schema_routes
from .debug import debug_routes

def register_routes(app):
    app.register_blueprint(upload_routes)
    app.register_blueprint(tree_routes)
    app.register_blueprint(event_routes)
    app.register_blueprint(people_routes)
    app.register_blueprint(timeline_routes)
    app.register_blueprint(schema_routes)
    app.register_blueprint(debug_routes)
