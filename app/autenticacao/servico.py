import os
from collections.abc import Mapping

from flask import session

from app.autorizacao import normalizar_papel


def carregar_usuarios_ambiente() -> dict[str, dict[str, str]]:
    usuarios: dict[str, dict[str, str]] = {}
    for indice in (1, 2, 3, 4, 5):
        email = os.getenv(f"AUTH_USER_{indice}_EMAIL", "").strip().lower()
        senha = os.getenv(f"AUTH_USER_{indice}_PASSWORD", "")
        papel = os.getenv(f"AUTH_USER_{indice}_PAPEL", "nao_editor")

        if email and senha:
            usuarios[email] = {"senha": senha, "papel": normalizar_papel(papel)}

    return usuarios


def autenticar(
    email: str,
    senha: str,
    usuarios_configurados: Mapping[str, Mapping[str, str]],
) -> dict[str, str] | None:
    email_normalizado = email.strip().lower()
    usuario = usuarios_configurados.get(email_normalizado)

    if not usuario:
        return None

    senha_esperada = str(usuario.get("senha", ""))
    if senha_esperada != senha:
        return None

    return {
        "email": email_normalizado,
        "papel": normalizar_papel(str(usuario.get("papel", "nao_editor"))),
    }


def registrar_sessao_usuario(email: str, papel: str) -> None:
    session["usuario_email"] = email
    session["papel_atual"] = normalizar_papel(papel)


def limpar_sessao_usuario() -> None:
    session.pop("usuario_email", None)
    session.pop("papel_atual", None)
