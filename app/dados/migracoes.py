from flask import Flask
from flask_migrate import stamp, upgrade
from sqlalchemy import inspect
from sqlalchemy import text

from .base import db

REVISAO_WIKI_INICIAL = "96097c95c490"
REVISAO_ATUAL = "2b4a1e6e5f9b"


def _definir_stamp_legado(tabelas: set[str]) -> str | None:
    if "wiki_paginas" in tabelas and "usuarios" in tabelas:
        return REVISAO_ATUAL

    if "wiki_paginas" in tabelas:
        return REVISAO_WIKI_INICIAL

    return None


def _historico_migracao_presente(tabelas: set[str]) -> bool:
    if "alembic_version" not in tabelas:
        return False

    with db.engine.connect() as conn:
        registro = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).fetchone()
        return registro is not None


def aplicar_upgrade_seguro(app: Flask) -> None:
    with app.app_context():
        tabelas = set(inspect(db.engine).get_table_names())
        revisao_stamp = None
        if not _historico_migracao_presente(tabelas):
            revisao_stamp = _definir_stamp_legado(tabelas)

        if revisao_stamp:
            stamp(revision=revisao_stamp)

        upgrade()
