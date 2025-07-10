from flask import Flask
from app.routes import main
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.register_blueprint(main)
    return app