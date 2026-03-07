import pytest

from app.autenticacao.servico import autenticar, bootstrap_admin_por_ambiente, criar_usuario
from app.dados.modelos import Usuario


@pytest.mark.unit
def test_autenticar_retorna_usuario_quando_credenciais_sao_validas(app_instance):
    with app_instance.app_context():
        criar_usuario("editor2@teste.local", "123456", papel="editor")

        usuario = autenticar("editor2@teste.local", "123456")

        assert usuario == {"email": "editor2@teste.local", "papel": "editor"}


@pytest.mark.unit
def test_autenticar_retorna_none_quando_senha_ou_email_invalidos(app_instance):
    with app_instance.app_context():
        criar_usuario("editor3@teste.local", "123456", papel="editor")

        assert autenticar("editor3@teste.local", "errada") is None
        assert autenticar("inexistente@teste.local", "123456") is None


@pytest.mark.unit
def test_bootstrap_admin_por_ambiente_cria_usuario(app_instance, monkeypatch):
    monkeypatch.setenv("AUTH_USER_ADMIN_EMAIL", "admin.bootstrap@teste.local")
    monkeypatch.setenv("AUTH_USER_ADMIN_PASSWORD", "abc123")
    monkeypatch.setenv("AUTH_USER_ADMIN_PAPEL", "admin")

    with app_instance.app_context():
        bootstrap_admin_por_ambiente()

        admin = Usuario.query.filter_by(email="admin.bootstrap@teste.local").first()
        assert admin is not None
        assert admin.papel == "admin"
        assert admin.validar_senha("abc123") is True
