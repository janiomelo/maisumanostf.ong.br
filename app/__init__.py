import os

from flask import Flask, g, session
from flask_talisman import Talisman

from .autenticacao import bootstrap_admin_por_ambiente
from .autenticacao.google_oauth import inicializar_google_oauth
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


def _ler_bool_env(chave: str, padrao: bool = False) -> bool:
    valor = os.getenv(chave)
    if valor is None:
        return padrao

    return valor.strip().lower() in {"1", "true", "t", "yes", "y", "on", "sim"}


def _montar_engine_options(database_uri: str, ambiente: str) -> dict:
    if not database_uri.startswith("postgresql+psycopg://"):
        return {}

    opcoes = {
        "pool_pre_ping": True,
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE_SECONDS", "300")),
    }

    if ambiente == "producao":
        opcoes["pool_use_lifo"] = True

    return opcoes


def _aplicar_migracoes_em_producao(app: Flask, ambiente: str) -> None:
    if app.config.get("TESTING", False):
        return

    if ambiente != "producao":
        return

    aplicar_upgrade_seguro(app)


def _configurar_headers_seguranca(app: Flask, ambiente: str) -> None:
    if not app.config.get("SECURITY_HEADERS_ENABLED", True):
        return

    force_https_padrao = ambiente == "producao" and not app.config.get("TESTING", False)
    force_https = app.config.get("TALISMAN_FORCE_HTTPS", force_https_padrao)

    politica_csp = app.config.get(
        "TALISMAN_CSP",
        {
            "default-src": ["'self'"],
            "img-src": ["'self'", "data:", "https:"],
            "script-src": ["'self'", "'unsafe-inline'", "https://www.googletagmanager.com", "https://cdn.jsdelivr.net"],
            "style-src": ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
            "connect-src": ["'self'", "https://www.google-analytics.com"],
            "font-src": ["'self'", "data:"],
            "object-src": ["'none'"],
            "base-uri": ["'self'"],
            "frame-ancestors": ["'none'"],
        },
    )

    Talisman(
        app,
        force_https=force_https,
        strict_transport_security=ambiente == "producao",
        session_cookie_secure=force_https,
        content_security_policy=politica_csp,
    )


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["GA4_MEASUREMENT_ID"] = os.getenv("GA4_MEASUREMENT_ID", "")
    app.config["GOOGLE_OAUTH_ENABLED"] = _ler_bool_env("GOOGLE_OAUTH_ENABLED", False)
    app.config["GOOGLE_CLIENT_ID"] = os.getenv("GOOGLE_CLIENT_ID", "")
    app.config["GOOGLE_CLIENT_SECRET"] = os.getenv("GOOGLE_CLIENT_SECRET", "")
    app.config["GOOGLE_REDIRECT_URI"] = os.getenv("GOOGLE_REDIRECT_URI", "").strip()
    app.config["GOOGLE_DISCOVERY_URL"] = os.getenv(
        "GOOGLE_DISCOVERY_URL", "https://accounts.google.com/.well-known/openid-configuration"
    )
    app.config["RESEND_API_KEY"] = os.getenv("RESEND_API_KEY", "")
    app.config["RESEND_FROM_EMAIL"] = os.getenv("RESEND_FROM_EMAIL", "")
    app.config["RESEND_REPLY_TO"] = os.getenv("RESEND_REPLY_TO", "")
    app.config["APOIOS_EMAIL_CONTATO"] = os.getenv("APOIOS_EMAIL_CONTATO", "")
    app.config["SITE_URL"] = os.getenv("SITE_URL", "")
    ambiente = os.getenv("AMBIENTE_APLICACAO", "desenvolvimento")
    database_url = os.getenv("DATABASE_URL", "")

    if test_config is None and ambiente == "producao" and not database_url:
        raise RuntimeError("DATABASE_URL obrigatoria em producao")

    fallback = "sqlite:////app/data/app.db"
    database_uri = _normalizar_database_url(database_url or fallback)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = _montar_engine_options(database_uri, ambiente)

    inicializar_google_oauth(app)

    if test_config:
        app.config.update(test_config)

    app.config.setdefault("SECURITY_HEADERS_ENABLED", _ler_bool_env("SECURITY_HEADERS_ENABLED", True))
    app.config.setdefault("TALISMAN_FORCE_HTTPS", _ler_bool_env("TALISMAN_FORCE_HTTPS", ambiente == "producao"))

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
    _configurar_headers_seguranca(app, ambiente)

    return app
