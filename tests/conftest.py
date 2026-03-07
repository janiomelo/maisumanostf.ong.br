import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.autenticacao import criar_usuario
from app import create_app


@pytest.fixture
def app_instance(tmp_path):
    banco_teste = tmp_path / "test.db"
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{banco_teste}",
        }
    )

    with app.app_context():
        criar_usuario("editor@teste.local", "123456", papel="editor")
        criar_usuario("admin@teste.local", "abc123", papel="admin")

    return app


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()
