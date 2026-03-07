import os

from flask import Flask

from .blueprints import register_blueprints


def create_app() -> Flask:
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    register_blueprints(app)

    return app
