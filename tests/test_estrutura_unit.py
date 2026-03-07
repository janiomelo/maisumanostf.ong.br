import pytest

from app import create_app, main
from app.dados.base import db


@pytest.mark.unit
def test_modulo_compatibilidade_expoe_componentes_legados():
    assert main.main_bp.name == "main"
    assert callable(main.get_setting)
    assert callable(main.parse_iso_date)
    assert callable(main.year_fraction)
    assert callable(main.format_br)
    assert callable(main.vacancy_dates)
    assert callable(main.build_chart_payload)
    assert callable(main._build_countdown_target)


@pytest.mark.unit
def test_factory_registra_blueprints_esperados():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    nomes = sorted(app.blueprints.keys())

    assert "main" in nomes
    assert "wiki" in nomes
    assert "apoios" in nomes
    assert "defesas" in nomes
    assert "admin" in nomes


@pytest.mark.unit
def test_factory_inicializa_extensao_db():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    assert "sqlalchemy" in app.extensions
    assert app.extensions["sqlalchemy"] is db
