import pytest
from sqlalchemy import inspect

import app as app_module
from app import _normalizar_database_url, create_app
from app.dados.base import db
from app.dados.modelos import WikiPagina


@pytest.mark.unit
def test_factory_registra_blueprints_esperados():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    nomes = sorted(app.blueprints.keys())

    assert "main" in nomes
    assert "autenticacao" in nomes
    assert "wiki" in nomes
    assert "apoios" in nomes
    assert "defesas" in nomes
    assert "admin" in nomes


@pytest.mark.unit
def test_factory_registra_comando_db_update_seguro():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    assert "db-update-seguro" in app.cli.commands


@pytest.mark.unit
def test_factory_inicializa_extensao_db():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    assert "sqlalchemy" in app.extensions
    assert app.extensions["sqlalchemy"] is db


@pytest.mark.unit
def test_seed_wiki_apenas_em_teste(tmp_path):
    banco_producao = tmp_path / "prod.db"
    app_prod = create_app(
        {
            "TESTING": False,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{banco_producao}",
        }
    )
    with app_prod.app_context():
        inspetor = inspect(db.engine)
        assert "wiki_paginas" not in inspetor.get_table_names()

    banco_teste = tmp_path / "test.db"
    app_test = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{banco_teste}",
        }
    )
    with app_test.app_context():
        assert WikiPagina.query.filter_by(slug="estatuto-basico-ampliado").first() is not None


@pytest.mark.unit
def test_normalizar_database_url_railway():
    raw = "postgres://user:pass@host:5432/dbname"
    assert _normalizar_database_url(raw) == "postgresql+psycopg://user:pass@host:5432/dbname"


@pytest.mark.unit
def test_normalizar_database_url_postgresql_sem_driver():
    raw = "postgresql://user:pass@host:5432/dbname"
    assert _normalizar_database_url(raw) == "postgresql+psycopg://user:pass@host:5432/dbname"


@pytest.mark.unit
def test_normalizar_database_url_preserva_quando_ja_tem_driver():
    raw = "postgresql+psycopg://user:pass@host:5432/dbname"
    assert _normalizar_database_url(raw) == raw


@pytest.mark.unit
def test_factory_aplica_migracoes_automaticas_em_producao(monkeypatch, tmp_path):
    banco_prod = tmp_path / "prod-migrate.db"
    monkeypatch.setenv("AMBIENTE_APLICACAO", "producao")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{banco_prod}")

    chamadas: list[str] = []

    def fake_aplicar_migracoes(app, ambiente):
        chamadas.append(ambiente)

    monkeypatch.setattr(app_module, "_aplicar_migracoes_em_producao", fake_aplicar_migracoes)

    create_app()

    assert chamadas == ["producao"]
