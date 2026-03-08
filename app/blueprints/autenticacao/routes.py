from flask import Blueprint, current_app, g, redirect, render_template, request, session, url_for

from app.autenticacao import (
    BancoIndisponivelError,
    GoogleOAuthError,
    autenticar,
    google_oauth_esta_configurado,
    limpar_sessao_usuario,
    obter_cliente_google,
    obter_ou_criar_usuario_google,
    remover_conta_usuario,
    registrar_sessao_usuario,
    trocar_codigo_por_usuario_google,
)

autenticacao_bp = Blueprint("autenticacao", __name__)


def _destino_seguro(destino: str) -> str:
    if destino.startswith("/") and not destino.startswith("//"):
        return destino

    return url_for("wiki.indice_wiki")


def _obter_callback_oauth_google() -> str:
    callback_configurada = str(current_app.config.get("GOOGLE_REDIRECT_URI", "")).strip()
    if callback_configurada:
        return callback_configurada

    return url_for("autenticacao.callback_oauth_google", _external=True)


@autenticacao_bp.get("/entrar")
def entrar():
    return render_template("autenticacao/entrar.html", erro=None, proximo=request.args.get("proximo", ""))


@autenticacao_bp.post("/entrar")
def processar_entrada():
    email = request.form.get("email", "")
    senha = request.form.get("senha", "")
    proximo = request.form.get("proximo", "")

    try:
        usuario = autenticar(email, senha)
    except BancoIndisponivelError:
        current_app.logger.exception("Falha de conexão com banco durante login")
        erro = "Serviço temporariamente indisponível. Tente novamente em instantes."
        return render_template("autenticacao/entrar.html", erro=erro, proximo=proximo), 503

    if not usuario:
        erro = "Credenciais inválidas. Verifique e tente novamente."
        return render_template("autenticacao/entrar.html", erro=erro, proximo=proximo), 401

    registrar_sessao_usuario(usuario["email"], usuario["papel"])
    destino = _destino_seguro(proximo or url_for("wiki.indice_wiki"))
    return redirect(destino)


@autenticacao_bp.get("/auth/google/iniciar")
def iniciar_oauth_google():
    if not google_oauth_esta_configurado(current_app.config):
        erro = "Login com Google indisponível no momento."
        return render_template("autenticacao/entrar.html", erro=erro, proximo=""), 200

    proximo = _destino_seguro(request.args.get("proximo", url_for("apoios.assinar_manifesto")))
    session["oauth_google_proximo"] = proximo

    try:
        cliente = obter_cliente_google()
        callback_url = _obter_callback_oauth_google()
        return cliente.authorize_redirect(callback_url, prompt="select_account")
    except GoogleOAuthError:
        current_app.logger.exception("Cliente OAuth Google não inicializado")
        erro = "Não foi possível iniciar o login com Google."
        return render_template("autenticacao/entrar.html", erro=erro, proximo=proximo), 200


@autenticacao_bp.get("/auth/google/callback")
def callback_oauth_google():
    proximo = _destino_seguro(session.pop("oauth_google_proximo", url_for("apoios.assinar_manifesto")))

    try:
        dados_usuario = trocar_codigo_por_usuario_google()
    except GoogleOAuthError:
        current_app.logger.exception("Falha no callback OAuth Google")
        erro = "Falha ao validar login com Google. Tente novamente."
        return render_template("autenticacao/entrar.html", erro=erro, proximo=proximo), 400

    if not dados_usuario.get("email") or not dados_usuario.get("sub"):
        erro = "Dados de autenticação inválidos retornados pelo Google."
        return render_template("autenticacao/entrar.html", erro=erro, proximo=proximo), 400

    if not dados_usuario.get("email_verified"):
        erro = "Sua conta Google precisa ter e-mail verificado para entrar."
        return render_template("autenticacao/entrar.html", erro=erro, proximo=proximo), 401

    try:
        usuario = obter_ou_criar_usuario_google(
            dados_usuario["sub"],
            dados_usuario["email"],
            bool(dados_usuario.get("email_verified", False)),
        )
    except Exception:
        current_app.logger.exception("Falha ao persistir/vincular usuário local após login Google")
        erro = "Não foi possível concluir o login com Google agora. Tente novamente em instantes."
        return render_template("autenticacao/entrar.html", erro=erro, proximo=proximo), 400

    registrar_sessao_usuario(usuario.email, usuario.papel)
    return redirect(proximo)


@autenticacao_bp.post("/sair")
def sair():
    limpar_sessao_usuario()
    return redirect(url_for("main.home"))


@autenticacao_bp.post("/conta/remover")
def remover_conta():
    email = str(getattr(g, "usuario_email", "") or "").strip().lower()
    if not email:
        return redirect(url_for("autenticacao.entrar"))

    remover_conta_usuario(email)
    limpar_sessao_usuario()
    return redirect(url_for("main.home"))


@autenticacao_bp.app_context_processor
def injetar_contexto_usuario() -> dict[str, str | bool | None]:
    return {
        "usuario_esta_logado": bool(getattr(g, "usuario_email", None)),
        "usuario_email": getattr(g, "usuario_email", None),
        "papel_atual": getattr(g, "papel_atual", "nao_editor"),
    }
