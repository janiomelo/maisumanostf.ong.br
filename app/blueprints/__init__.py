from flask import Flask

from .admin.routes import admin_bp
from .apoios.routes import apoios_bp
from .defesas.routes import defesas_bp
from .publico.routes import publico_bp
from .wiki.routes import wiki_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(publico_bp)
    app.register_blueprint(wiki_bp)
    app.register_blueprint(apoios_bp)
    app.register_blueprint(defesas_bp)
    app.register_blueprint(admin_bp)
