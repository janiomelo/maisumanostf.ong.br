import os

from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    from .main import main_bp

    app.register_blueprint(main_bp)

    return app
