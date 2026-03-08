import os

from flask import Flask, g, session

from .autenticacao import bootstrap_admin_por_ambiente
from .autorizacao import normalizar_papel
from .blueprints import register_blueprints
from .cli.db import registrar_comandos_db
from .cli.usuarios import registrar_comandos_usuarios
from .dados import inicializar_camada_de_dados
from .dados.migracoes import aplicar_upgrade_seguro


def _normalizar_database_url(raw_url: str) -> str:
    if raw_url.startswith("postgresql+psycopg://"):
        return raw_url

    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)

    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql+psycopg://", 1)

    return raw_url


def _aplicar_migracoes_em_producao(app: Flask, ambiente: str) -> None:
    if app.config.get("TESTING", False):
        return

    if ambiente != "producao":
        return

    aplicar_upgrade_seguro(app)


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["GA4_MEASUREMENT_ID"] = os.getenv("GA4_MEASUREMENT_ID", "")
    ambiente = os.getenv("AMBIENTE_APLICACAO", "desenvolvimento")
    database_url = os.getenv("DATABASE_URL", "")

    if test_config is None and ambiente == "producao" and not database_url:
        raise RuntimeError("DATABASE_URL obrigatoria em producao")

    fallback = "sqlite:////app/data/app.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = _normalizar_database_url(database_url or fallback)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if test_config:
        app.config.update(test_config)

    @app.before_request
    def carregar_contexto_autenticacao() -> None:
        g.usuario_email = session.get("usuario_email")
        g.papel_atual = normalizar_papel(session.get("papel_atual"))

    inicializar_camada_de_dados(app)
    registrar_comandos_db(app)
    registrar_comandos_usuarios(app)
    _aplicar_migracoes_em_producao(app, ambiente)

    if not app.config.get("TESTING", False):
        with app.app_context():
            bootstrap_admin_por_ambiente()

    register_blueprints(app)

    return app
