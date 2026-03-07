import os

from flask import Flask

from .blueprints import register_blueprints
from .dados import inicializar_camada_de_dados


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:////app/data/app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if test_config:
        app.config.update(test_config)

    inicializar_camada_de_dados(app)
    register_blueprints(app)

    return app
