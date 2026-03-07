import os

from flask import Flask

from .blueprints import register_blueprints
from .dados import inicializar_camada_de_dados


def _normalizar_database_url(raw_url: str) -> str:
    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql://", 1)
    return raw_url


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    ambiente = os.getenv("AMBIENTE_APLICACAO", "desenvolvimento")
    database_url = os.getenv("DATABASE_URL", "")

    if test_config is None and ambiente == "producao" and not database_url:
        raise RuntimeError("DATABASE_URL obrigatoria em producao")

    fallback = "sqlite:////app/data/app.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = _normalizar_database_url(database_url or fallback)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if test_config:
        app.config.update(test_config)

    inicializar_camada_de_dados(app)
    register_blueprints(app)

    return app
