from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def inicializar_camada_de_dados(app: Flask) -> None:
    db.init_app(app)

    with app.app_context():
        from . import modelos  # noqa: F401
        from .semente import semear_wiki_inicial

        db.create_all()
        semear_wiki_inicial()
