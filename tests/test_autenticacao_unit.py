import pytest

from app.autenticacao.servico import autenticar, carregar_usuarios_ambiente


@pytest.mark.unit
def test_autenticar_retorna_usuario_quando_credenciais_sao_validas():
    usuarios = {
        "editor@teste.local": {"senha": "123456", "papel": "editor"},
    }

    usuario = autenticar("editor@teste.local", "123456", usuarios)

    assert usuario == {"email": "editor@teste.local", "papel": "editor"}


@pytest.mark.unit
def test_autenticar_retorna_none_quando_senha_ou_email_invalidos():
    usuarios = {
        "editor@teste.local": {"senha": "123456", "papel": "editor"},
    }

    assert autenticar("editor@teste.local", "errada", usuarios) is None
    assert autenticar("inexistente@teste.local", "123456", usuarios) is None


@pytest.mark.unit
def test_carregar_usuarios_ambiente_ler_blocos_configurados(monkeypatch):
    monkeypatch.setenv("AUTH_USER_1_EMAIL", "admin@teste.local")
    monkeypatch.setenv("AUTH_USER_1_PASSWORD", "abc123")
    monkeypatch.setenv("AUTH_USER_1_PAPEL", "admin")

    monkeypatch.setenv("AUTH_USER_2_EMAIL", "editor@teste.local")
    monkeypatch.setenv("AUTH_USER_2_PASSWORD", "123456")
    monkeypatch.setenv("AUTH_USER_2_PAPEL", "editor")

    usuarios = carregar_usuarios_ambiente()

    assert usuarios["admin@teste.local"]["papel"] == "admin"
    assert usuarios["editor@teste.local"]["senha"] == "123456"
