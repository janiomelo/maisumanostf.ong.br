import pytest

import app.comunicacao.apoios as comunicacao_apoios
import app.comunicacao.resend as cliente_resend
from app.comunicacao.apoios import ASSUNTO_CONFIRMACAO_APOIO, enviar_email_confirmacao_apoio, montar_html_confirmacao_apoio
from app.comunicacao.resend import ErroClienteResend, enviar_email_resend


@pytest.mark.unit
def test_montar_html_confirmacao_apoio_tem_texto_obrigatorio(app_instance):
    with app_instance.app_context():
        html = montar_html_confirmacao_apoio(
            destinatario="apoiadora@teste.local",
            nome_publico="Apoiadora Teste",
            ordem_apoio=5,
            canal_contato="contato@maisumanostf.ong.br",
            site_publico="https://maisumanostf.ong.br",
        )

    assert "Obrigada por apoiar o manifesto" in html
    assert "Seu apoio é o <strong>5º</strong>" in html
    assert "Escopo de aceite" in html
    assert "exclusivo para o conteúdo deste e-mail" in html
    assert "contato@maisumanostf.ong.br" in html
    assert "Apoiadora Teste" in html
    assert "https://maisumanostf.ong.br/apoios/assinar" in html


@pytest.mark.unit
def test_enviar_email_confirmacao_apoio_retorna_none_sem_configuracao_resend(monkeypatch):
    chamado = {"valor": False}

    def falso_envio(**kwargs):
        chamado["valor"] = True
        return "id-123"

    monkeypatch.setattr(comunicacao_apoios, "enviar_email_resend", falso_envio)

    resultado = enviar_email_confirmacao_apoio(
        config={"RESEND_API_KEY": "", "RESEND_FROM_EMAIL": ""},
        destinatario="apoiadora@teste.local",
        nome_publico="",
        ordem_apoio=1,
        url_site="https://maisumanostf.ong.br",
    )

    assert resultado is None
    assert chamado["valor"] is False


@pytest.mark.unit
def test_enviar_email_confirmacao_apoio_encaminha_payload_para_resend(app_instance, monkeypatch):
    captura = {}

    def falso_envio(**kwargs):
        captura.update(kwargs)
        return "email-id-abc"

    monkeypatch.setattr(comunicacao_apoios, "enviar_email_resend", falso_envio)

    with app_instance.app_context():
        resultado = enviar_email_confirmacao_apoio(
            config={
                "RESEND_API_KEY": "chave",
                "RESEND_FROM_EMAIL": "Equipe <apoios@maisumanostf.ong.br>",
                "RESEND_REPLY_TO": "resposta@maisumanostf.ong.br",
                "APOIOS_EMAIL_CONTATO": "canal@maisumanostf.ong.br",
                "SITE_URL": "https://maisumanostf.ong.br",
            },
            destinatario="apoiadora@teste.local",
            nome_publico="Nome Publico",
            ordem_apoio=7,
            url_site="http://ignorado.local",
        )

    assert resultado == "email-id-abc"
    assert captura["api_key"] == "chave"
    assert captura["remetente"] == "Equipe <apoios@maisumanostf.ong.br>"
    assert captura["destinatario"] == "apoiadora@teste.local"
    assert captura["assunto"] == ASSUNTO_CONFIRMACAO_APOIO
    assert captura["reply_to"] == "resposta@maisumanostf.ong.br"
    assert "Escopo de aceite" in captura["html"]
    assert "<strong>7º</strong>" in captura["html"]


@pytest.mark.unit
def test_enviar_email_resend_dispara_erro_em_status_http_nao_sucesso(monkeypatch):
    class RespostaFalsa:
        status_code = 422

        @staticmethod
        def json():
            return {"message": "payload invalido"}

    monkeypatch.setattr(cliente_resend.requests, "post", lambda *args, **kwargs: RespostaFalsa())

    with pytest.raises(ErroClienteResend, match="payload invalido"):
        enviar_email_resend(
            api_key="chave",
            remetente="Equipe <apoios@maisumanostf.ong.br>",
            destinatario="apoiadora@teste.local",
            assunto="Assunto",
            html="<p>Teste</p>",
        )


@pytest.mark.unit
def test_enviar_email_resend_retorna_id_em_sucesso(monkeypatch):
    class RespostaFalsa:
        status_code = 200

        @staticmethod
        def json():
            return {"id": " email-id-001 "}

    chamada = {}

    def post_falso(url, **kwargs):
        chamada["url"] = url
        chamada.update(kwargs)
        return RespostaFalsa()

    monkeypatch.setattr(cliente_resend.requests, "post", post_falso)

    mensagem_id = enviar_email_resend(
        api_key="chave",
        remetente="Equipe <apoios@maisumanostf.ong.br>",
        destinatario="apoiadora@teste.local",
        assunto="Assunto",
        html="<p>Teste</p>",
    )

    assert mensagem_id == "email-id-001"
    assert chamada["url"] == "https://api.resend.com/emails"
    assert chamada["headers"]["Authorization"] == "Bearer chave"
    assert chamada["json"]["to"] == ["apoiadora@teste.local"]
    assert "reply_to" not in chamada["json"]


@pytest.mark.unit
def test_enviar_email_resend_inclui_reply_to_no_payload(monkeypatch):
    class RespostaFalsa:
        status_code = 200

        @staticmethod
        def json():
            return {"id": "ok"}

    chamada = {}

    def post_falso(url, **kwargs):
        chamada.update(kwargs)
        return RespostaFalsa()

    monkeypatch.setattr(cliente_resend.requests, "post", post_falso)

    enviar_email_resend(
        api_key="chave",
        remetente="Equipe <apoios@maisumanostf.ong.br>",
        destinatario="apoiadora@teste.local",
        assunto="Assunto",
        html="<p>Teste</p>",
        reply_to="resposta@maisumanostf.ong.br",
    )

    assert chamada["json"]["reply_to"] == "resposta@maisumanostf.ong.br"


@pytest.mark.unit
@pytest.mark.parametrize(
    "api_key,remetente,destinatario,mensagem",
    [
        ("", "Equipe <apoios@maisumanostf.ong.br>", "apoiadora@teste.local", "RESEND_API_KEY e obrigatoria"),
        ("chave", "", "apoiadora@teste.local", "RESEND_FROM_EMAIL e obrigatorio"),
        ("chave", "Equipe <apoios@maisumanostf.ong.br>", "", "Destinatario e obrigatorio"),
    ],
)
def test_enviar_email_resend_valida_campos_obrigatorios(api_key, remetente, destinatario, mensagem):
    with pytest.raises(ValueError, match=mensagem):
        enviar_email_resend(
            api_key=api_key,
            remetente=remetente,
            destinatario=destinatario,
            assunto="Assunto",
            html="<p>Teste</p>",
        )


@pytest.mark.unit
def test_enviar_email_resend_dispara_erro_quando_sucesso_sem_id(monkeypatch):
    class RespostaFalsa:
        status_code = 200

        @staticmethod
        def json():
            return {}

    monkeypatch.setattr(cliente_resend.requests, "post", lambda *args, **kwargs: RespostaFalsa())

    with pytest.raises(ErroClienteResend, match="sucesso sem id de mensagem"):
        enviar_email_resend(
            api_key="chave",
            remetente="Equipe <apoios@maisumanostf.ong.br>",
            destinatario="apoiadora@teste.local",
            assunto="Assunto",
            html="<p>Teste</p>",
        )


@pytest.mark.unit
def test_enviar_email_resend_dispara_erro_padrao_quando_resposta_nao_e_json(monkeypatch):
    class RespostaFalsa:
        status_code = 500

        @staticmethod
        def json():
            raise ValueError("sem json")

    monkeypatch.setattr(cliente_resend.requests, "post", lambda *args, **kwargs: RespostaFalsa())

    with pytest.raises(ErroClienteResend, match="status 500"):
        enviar_email_resend(
            api_key="chave",
            remetente="Equipe <apoios@maisumanostf.ong.br>",
            destinatario="apoiadora@teste.local",
            assunto="Assunto",
            html="<p>Teste</p>",
        )


@pytest.mark.unit
def test_enviar_email_resend_dispara_erro_padrao_quando_json_sem_message_ou_error(monkeypatch):
    class RespostaFalsa:
        status_code = 429

        @staticmethod
        def json():
            return {"detalhe": "limite"}

    monkeypatch.setattr(cliente_resend.requests, "post", lambda *args, **kwargs: RespostaFalsa())

    with pytest.raises(ErroClienteResend, match="status 429"):
        enviar_email_resend(
            api_key="chave",
            remetente="Equipe <apoios@maisumanostf.ong.br>",
            destinatario="apoiadora@teste.local",
            assunto="Assunto",
            html="<p>Teste</p>",
        )
