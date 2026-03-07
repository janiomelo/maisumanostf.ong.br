import os
from collections.abc import Mapping

from flask import session

from app.autorizacao import normalizar_papel


def carregar_usuarios_ambiente() -> dict[str, dict[str, str]]:
    usuarios: dict[str, dict[str, str]] = {}

    email_admin = os.getenv("AUTH_USER_ADMIN_EMAIL", "").strip().lower()
    senha_admin = os.getenv("AUTH_USER_ADMIN_PASSWORD", "")
    papel_admin = os.getenv("AUTH_USER_ADMIN_PAPEL", "admin")

    if email_admin and senha_admin:
        usuarios[email_admin] = {
            "senha": senha_admin,
            "papel": normalizar_papel(papel_admin),
        }

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
