import pytest
from sqlalchemy.exc import OperationalError

import app.autenticacao.servico as servico_autenticacao
from app.autenticacao.servico import (
    BancoIndisponivelError,
    atualizar_usuario,
    autenticar,
    bootstrap_admin_por_ambiente,
    definir_usuario_ativo,
    criar_usuario,
    limpar_sessao_usuario,
    obter_ou_criar_usuario_google,
    registrar_sessao_usuario,
)
from app.dados.modelos import Usuario
import app.blueprints.autenticacao.routes as rotas_autenticacao


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

        assert autenticar("", "123456") is None
        assert autenticar("editor3@teste.local", "") is None
        assert autenticar("editor3@teste.local", "errada") is None
        assert autenticar("inexistente@teste.local", "123456") is None


@pytest.mark.unit
def test_autenticar_dispara_erro_de_banco_indisponivel_quando_operational_error(app_instance, monkeypatch):
    class QueryQueFalha:
        def filter_by(self, **kwargs):
            return self

        def first(self):
            raise OperationalError("select", {}, Exception("falha simulada"))

    with app_instance.app_context():
        query_original = servico_autenticacao.Usuario.query
        monkeypatch.setattr(servico_autenticacao.Usuario, "query", QueryQueFalha(), raising=False)

        with pytest.raises(BancoIndisponivelError):
            autenticar("editor@teste.local", "123456")

        monkeypatch.setattr(servico_autenticacao.Usuario, "query", query_original, raising=False)


@pytest.mark.unit
def test_login_retorna_503_quando_banco_esta_indisponivel(client, monkeypatch):
    monkeypatch.setattr(
        rotas_autenticacao,
        "autenticar",
        lambda email, senha: (_ for _ in ()).throw(BancoIndisponivelError("falha")),
    )

    response = client.post(
        "/entrar",
        data={"email": "editor@teste.local", "senha": "123456"},
    )

    assert response.status_code == 503
    html = response.get_data(as_text=True)
    assert "Servico temporariamente indisponivel" in html


@pytest.mark.unit
def test_criar_usuario_valida_email_e_senha_obrigatorios(app_instance):
    with app_instance.app_context():
        with pytest.raises(ValueError, match="Email e obrigatorio"):
            criar_usuario("   ", "123456", papel="editor")

        with pytest.raises(ValueError, match="Senha e obrigatoria"):
            criar_usuario("novo@teste.local", "", papel="editor")


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


@pytest.mark.unit
def test_bootstrap_admin_por_ambiente_nao_faz_nada_sem_credenciais(app_instance, monkeypatch):
    monkeypatch.delenv("AUTH_USER_ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("AUTH_USER_ADMIN_PASSWORD", raising=False)

    with app_instance.app_context():
        quantidade_antes = Usuario.query.count()
        bootstrap_admin_por_ambiente()
        assert Usuario.query.count() == quantidade_antes


@pytest.mark.unit
def test_bootstrap_admin_por_ambiente_retorna_se_admin_ja_existe(app_instance, monkeypatch):
    monkeypatch.setenv("AUTH_USER_ADMIN_EMAIL", "admin@teste.local")
    monkeypatch.setenv("AUTH_USER_ADMIN_PASSWORD", "abc123")

    with app_instance.app_context():
        quantidade_antes = Usuario.query.count()
        bootstrap_admin_por_ambiente()
        assert Usuario.query.count() == quantidade_antes


@pytest.mark.unit
def test_bootstrap_admin_por_ambiente_ignora_falha_de_tabela(app_instance, monkeypatch):
    monkeypatch.setenv("AUTH_USER_ADMIN_EMAIL", "admin.operational@teste.local")
    monkeypatch.setenv("AUTH_USER_ADMIN_PASSWORD", "abc123")

    class QueryQueFalha:
        def filter_by(self, **kwargs):
            return self

        def one(self):
            raise OperationalError("select", {}, Exception("falha simulada"))

    with app_instance.app_context():
        query_original = servico_autenticacao.Usuario.query
        monkeypatch.setattr(servico_autenticacao.Usuario, "query", QueryQueFalha(), raising=False)

        bootstrap_admin_por_ambiente()

        monkeypatch.setattr(servico_autenticacao.Usuario, "query", query_original, raising=False)


@pytest.mark.unit
def test_registrar_e_limpar_sessao_usuario(app_instance):
    with app_instance.test_request_context("/"):
        registrar_sessao_usuario("sessao@teste.local", "editor")
        assert servico_autenticacao.session.get("usuario_email") == "sessao@teste.local"
        assert servico_autenticacao.session.get("papel_atual") == "editor"

        limpar_sessao_usuario()
        assert servico_autenticacao.session.get("usuario_email") is None
        assert servico_autenticacao.session.get("papel_atual") is None


@pytest.mark.unit
def test_atualizar_usuario_inexistente_retorna_erro(app_instance):
    with app_instance.app_context():
        with pytest.raises(ValueError, match="Usuario nao encontrado"):
            atualizar_usuario(usuario_id=9999, papel="editor", senha="")


@pytest.mark.unit
def test_definir_usuario_ativo_inexistente_retorna_erro(app_instance):
    with app_instance.app_context():
        with pytest.raises(ValueError, match="Usuario nao encontrado"):
            definir_usuario_ativo(usuario_id=9999, ativo=False)


@pytest.mark.unit
def test_obter_ou_criar_usuario_google_cria_novo_usuario(app_instance):
    with app_instance.app_context():
        usuario = obter_ou_criar_usuario_google(
            sub="google-sub-abc",
            email="novo.google@teste.local",
            email_verificado=True,
        )

        assert usuario.email == "novo.google@teste.local"
        assert usuario.google_sub == "google-sub-abc"
        assert usuario.origem_auth == "google"
        assert usuario.email_verificado is True


@pytest.mark.unit
def test_obter_ou_criar_usuario_google_vincula_usuario_existente_por_email(app_instance):
    with app_instance.app_context():
        criar_usuario("editor.google@teste.local", "123456", papel="editor")

        usuario = obter_ou_criar_usuario_google(
            sub="google-sub-link",
            email="editor.google@teste.local",
            email_verificado=True,
        )

        assert usuario.email == "editor.google@teste.local"
        assert usuario.google_sub == "google-sub-link"
        assert usuario.origem_auth == "google"
