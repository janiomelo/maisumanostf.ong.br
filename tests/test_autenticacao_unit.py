import pytest
from sqlalchemy.exc import OperationalError
from flask import Flask

import app.autenticacao.servico as servico_autenticacao
import app.autenticacao.google_oauth as google_oauth_mod
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
from app.autenticacao.google_oauth import GoogleOAuthError


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
    assert "Serviço temporariamente indisponível" in html


@pytest.mark.unit
def test_criar_usuario_valida_email_e_senha_obrigatorios(app_instance):
    with app_instance.app_context():
        with pytest.raises(ValueError, match="E-mail é obrigatório"):
            criar_usuario("   ", "123456", papel="editor")

        with pytest.raises(ValueError, match="Senha é obrigatória"):
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
        with pytest.raises(ValueError, match="Usuário não encontrado"):
            atualizar_usuario(usuario_id=9999, papel="editor", senha="")


@pytest.mark.unit
def test_definir_usuario_ativo_inexistente_retorna_erro(app_instance):
    with app_instance.app_context():
        with pytest.raises(ValueError, match="Usuário não encontrado"):
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


@pytest.mark.functional
def test_oauth_google_iniciar_retorna_mensagem_amigavel_quando_cliente_nao_inicializa(client, monkeypatch):
    client.application.config["GOOGLE_OAUTH_ENABLED"] = True
    client.application.config["GOOGLE_CLIENT_ID"] = "id"
    client.application.config["GOOGLE_CLIENT_SECRET"] = "secret"

    monkeypatch.setattr(
        rotas_autenticacao,
        "obter_cliente_google",
        lambda: (_ for _ in ()).throw(GoogleOAuthError("falha")),
    )

    response = client.get("/auth/google/iniciar")

    assert response.status_code == 200
    assert "Não foi possível iniciar o login com Google" in response.get_data(as_text=True)


@pytest.mark.functional
def test_oauth_google_iniciar_usa_redirect_uri_configurada(client, monkeypatch):
    client.application.config["GOOGLE_OAUTH_ENABLED"] = True
    client.application.config["GOOGLE_CLIENT_ID"] = "id"
    client.application.config["GOOGLE_CLIENT_SECRET"] = "secret"
    client.application.config["GOOGLE_REDIRECT_URI"] = "https://maisumanostf.ong.br/auth/google/callback"

    class ClienteGoogleFalso:
        @staticmethod
        def authorize_redirect(callback_url, prompt=None):
            assert callback_url == "https://maisumanostf.ong.br/auth/google/callback"
            assert prompt == "select_account"
            return "ok"

    monkeypatch.setattr(rotas_autenticacao, "obter_cliente_google", lambda: ClienteGoogleFalso())

    response = client.get("/auth/google/iniciar")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "ok"


@pytest.mark.functional
def test_oauth_google_iniciar_usa_callback_externa_quando_redirect_uri_nao_configurada(client, monkeypatch):
    client.application.config["GOOGLE_OAUTH_ENABLED"] = True
    client.application.config["GOOGLE_CLIENT_ID"] = "id"
    client.application.config["GOOGLE_CLIENT_SECRET"] = "secret"
    client.application.config["GOOGLE_REDIRECT_URI"] = ""

    class ClienteGoogleFalso:
        @staticmethod
        def authorize_redirect(callback_url, prompt=None):
            assert callback_url.endswith("/auth/google/callback")
            assert callback_url.startswith("http")
            return "ok"

    monkeypatch.setattr(rotas_autenticacao, "obter_cliente_google", lambda: ClienteGoogleFalso())

    response = client.get("/auth/google/iniciar")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "ok"


@pytest.mark.functional
def test_oauth_google_callback_retorna_400_quando_troca_codigo_falha(client, monkeypatch):
    monkeypatch.setattr(
        rotas_autenticacao,
        "trocar_codigo_por_usuario_google",
        lambda: (_ for _ in ()).throw(GoogleOAuthError("falha")),
    )

    response = client.get("/auth/google/callback")

    assert response.status_code == 400
    assert "Falha ao validar login com Google" in response.get_data(as_text=True)


@pytest.mark.functional
def test_oauth_google_callback_retorna_400_quando_google_nao_envia_sub_ou_email(client, monkeypatch):
    monkeypatch.setattr(
        rotas_autenticacao,
        "trocar_codigo_por_usuario_google",
        lambda: {"sub": "", "email": "", "email_verified": True, "name": "Sem dados"},
    )

    response = client.get("/auth/google/callback")

    assert response.status_code == 400
    assert "Dados de autenticação inválidos retornados pelo Google" in response.get_data(as_text=True)


@pytest.mark.unit
def test_google_oauth_configurado_exige_flags_e_credenciais():
    assert google_oauth_mod.google_oauth_esta_configurado({}) is False
    assert (
        google_oauth_mod.google_oauth_esta_configurado(
            {
                "GOOGLE_OAUTH_ENABLED": True,
                "GOOGLE_CLIENT_ID": "id",
                "GOOGLE_CLIENT_SECRET": "secret",
            }
        )
        is True
    )


@pytest.mark.unit
def test_inicializar_google_oauth_nao_registra_cliente_quando_nao_configurado(monkeypatch):
    app = Flask(__name__)
    app.config.update(
        {
            "GOOGLE_OAUTH_ENABLED": False,
            "GOOGLE_CLIENT_ID": "",
            "GOOGLE_CLIENT_SECRET": "",
            "GOOGLE_DISCOVERY_URL": "https://accounts.google.com/.well-known/openid-configuration",
        }
    )

    chamadas = {"init_app": 0, "register": 0}

    monkeypatch.setattr(
        google_oauth_mod.oauth,
        "init_app",
        lambda flask_app: chamadas.__setitem__("init_app", chamadas["init_app"] + 1),
    )
    monkeypatch.setattr(
        google_oauth_mod.oauth,
        "register",
        lambda **kwargs: chamadas.__setitem__("register", chamadas["register"] + 1),
    )

    google_oauth_mod.inicializar_google_oauth(app)

    assert chamadas == {"init_app": 1, "register": 0}


@pytest.mark.unit
def test_inicializar_google_oauth_registra_cliente_quando_configurado(monkeypatch):
    app = Flask(__name__)
    app.config.update(
        {
            "GOOGLE_OAUTH_ENABLED": True,
            "GOOGLE_CLIENT_ID": "id",
            "GOOGLE_CLIENT_SECRET": "secret",
            "GOOGLE_DISCOVERY_URL": "https://accounts.google.com/.well-known/openid-configuration",
        }
    )

    registro = {}
    monkeypatch.setattr(google_oauth_mod.oauth, "init_app", lambda flask_app: None)
    monkeypatch.setattr(
        google_oauth_mod.oauth,
        "register",
        lambda **kwargs: registro.update(kwargs),
    )

    google_oauth_mod.inicializar_google_oauth(app)

    assert registro["name"] == "google"
    assert registro["client_id"] == "id"
    assert registro["client_secret"] == "secret"
    assert registro["server_metadata_url"] == "https://accounts.google.com/.well-known/openid-configuration"


@pytest.mark.unit
def test_obter_cliente_google_dispara_erro_quando_cliente_nao_existe(monkeypatch):
    monkeypatch.setattr(google_oauth_mod.oauth, "create_client", lambda nome: None)

    with pytest.raises(GoogleOAuthError, match="nao inicializado"):
        google_oauth_mod.obter_cliente_google()


@pytest.mark.unit
def test_obter_cliente_google_retorna_cliente_quando_disponivel(monkeypatch):
    cliente_falso = object()
    monkeypatch.setattr(google_oauth_mod.oauth, "create_client", lambda nome: cliente_falso)

    assert google_oauth_mod.obter_cliente_google() is cliente_falso


@pytest.mark.unit
def test_trocar_codigo_por_usuario_google_retorna_userinfo_do_token(monkeypatch):
    class ClienteGoogleFalso:
        @staticmethod
        def authorize_access_token():
            return {
                "userinfo": {
                    "sub": "sub-1",
                    "email": "USER@TESTE.LOCAL ",
                    "email_verified": True,
                    "name": "  Usuario Teste  ",
                }
            }

    monkeypatch.setattr(google_oauth_mod, "obter_cliente_google", lambda: ClienteGoogleFalso())

    dados = google_oauth_mod.trocar_codigo_por_usuario_google()

    assert dados == {
        "sub": "sub-1",
        "email": "user@teste.local",
        "email_verified": True,
        "name": "Usuario Teste",
    }


@pytest.mark.unit
def test_trocar_codigo_por_usuario_google_consulta_userinfo_quando_token_sem_campo(monkeypatch):
    class RespostaJsonFalsa:
        @staticmethod
        def json():
            return {
                "sub": "sub-2",
                "email": "via.userinfo@teste.local",
                "email_verified": False,
                "name": "Via Userinfo",
            }

    class ClienteGoogleFalso:
        @staticmethod
        def authorize_access_token():
            return {"access_token": "abc"}

        @staticmethod
        def userinfo(token=None):
            assert token == {"access_token": "abc"}
            return RespostaJsonFalsa()

    monkeypatch.setattr(google_oauth_mod, "obter_cliente_google", lambda: ClienteGoogleFalso())

    dados = google_oauth_mod.trocar_codigo_por_usuario_google()

    assert dados["sub"] == "sub-2"
    assert dados["email"] == "via.userinfo@teste.local"
    assert dados["email_verified"] is False


@pytest.mark.unit
def test_trocar_codigo_por_usuario_google_dispara_erro_quando_token_falha(monkeypatch):
    class ClienteGoogleFalso:
        @staticmethod
        def authorize_access_token():
            raise RuntimeError("falha token")

    monkeypatch.setattr(google_oauth_mod, "obter_cliente_google", lambda: ClienteGoogleFalso())

    with pytest.raises(GoogleOAuthError, match="token de acesso"):
        google_oauth_mod.trocar_codigo_por_usuario_google()


@pytest.mark.unit
def test_trocar_codigo_por_usuario_google_dispara_erro_quando_userinfo_falha(monkeypatch):
    class ClienteGoogleFalso:
        @staticmethod
        def authorize_access_token():
            return "token-simples"

        @staticmethod
        def userinfo(token=None):
            raise RuntimeError("falha userinfo")

    monkeypatch.setattr(google_oauth_mod, "obter_cliente_google", lambda: ClienteGoogleFalso())

    with pytest.raises(GoogleOAuthError, match="consultar perfil"):
        google_oauth_mod.trocar_codigo_por_usuario_google()


@pytest.mark.unit
def test_trocar_codigo_por_usuario_google_dispara_erro_quando_resposta_final_invalida(monkeypatch):
    class ClienteGoogleFalso:
        @staticmethod
        def authorize_access_token():
            return {"access_token": "abc"}

        @staticmethod
        def userinfo(token=None):
            return "nao-dict"

    monkeypatch.setattr(google_oauth_mod, "obter_cliente_google", lambda: ClienteGoogleFalso())

    with pytest.raises(GoogleOAuthError, match="Resposta invalida"):
        google_oauth_mod.trocar_codigo_por_usuario_google()
