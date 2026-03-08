from flask import Blueprint, current_app, g, redirect, render_template, request, url_for

from app.autenticacao import (
    BancoIndisponivelError,
    autenticar,
    limpar_sessao_usuario,
    registrar_sessao_usuario,
)

autenticacao_bp = Blueprint("autenticacao", __name__)


def _destino_seguro(destino: str) -> str:
    if destino.startswith("/") and not destino.startswith("//"):
        return destino

    return url_for("wiki.indice_wiki")


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
        current_app.logger.exception("Falha de conexao com banco durante login")
        erro = "Servico temporariamente indisponivel. Tente novamente em instantes."
        return render_template("autenticacao/entrar.html", erro=erro, proximo=proximo), 503

    if not usuario:
        erro = "Credenciais invalidas. Verifique e tente novamente."
        return render_template("autenticacao/entrar.html", erro=erro, proximo=proximo), 401

    registrar_sessao_usuario(usuario["email"], usuario["papel"])
    destino = _destino_seguro(proximo or url_for("wiki.indice_wiki"))
    return redirect(destino)


@autenticacao_bp.post("/sair")
def sair():
    limpar_sessao_usuario()
    return redirect(url_for("main.home"))


@autenticacao_bp.app_context_processor
def injetar_contexto_usuario() -> dict[str, str | bool | None]:
    return {
        "usuario_esta_logado": bool(getattr(g, "usuario_email", None)),
        "usuario_email": getattr(g, "usuario_email", None),
        "papel_atual": getattr(g, "papel_atual", "nao_editor"),
    }
