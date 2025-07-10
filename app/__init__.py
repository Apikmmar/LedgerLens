from flask import Flask
from app.routes import register_routes
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    register_routes(app)
    return app
