import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.autenticacao import criar_usuario
from app import create_app
import app.comunicacao.resend as resend_mod


@pytest.fixture
def app_instance(tmp_path):
    banco_teste = tmp_path / "test.db"
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{banco_teste}",
            "RESEND_API_KEY": "",
            "RESEND_FROM_EMAIL": "",
            "RESEND_REPLY_TO": "",
            "APOIOS_EMAIL_CONTATO": "",
            "SITE_URL": "http://localhost",
        }
    )

    with app.app_context():
        criar_usuario("editor@teste.local", "123456", papel="editor")
        criar_usuario("admin@teste.local", "abc123", papel="admin")

    return app


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


@pytest.fixture(autouse=True)
def bloquear_envio_resend_real(monkeypatch):
    def _post_bloqueado(*args, **kwargs):
        raise AssertionError("Envio real para Resend bloqueado durante testes")

    monkeypatch.setattr(resend_mod.requests, "post", _post_bloqueado)
