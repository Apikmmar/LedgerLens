from .main_routes import main_routes
from .receipt_routes import receipt_routes

def register_routes(app):
    app.register_blueprint(main_routes)
    app.register_blueprint(receipt_routes)