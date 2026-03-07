from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()


def inicializar_camada_de_dados(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)

    from . import modelos  # noqa: F401

    if app.config.get("TESTING", False):
        with app.app_context():
            from .semente import semear_wiki_inicial

            db.create_all()
            semear_wiki_inicial()
