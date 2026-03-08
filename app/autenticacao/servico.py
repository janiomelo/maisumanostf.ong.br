import os

from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm.exc import NoResultFound
from flask import session

from app.autorizacao import normalizar_papel
from app.dados.base import db
from app.dados.modelos import Usuario


class BancoIndisponivelError(RuntimeError):
    pass


def autenticar(email: str, senha: str) -> dict[str, str] | None:
    email_normalizado = email.strip().lower()
    if not email_normalizado or not senha:
        return None

    try:
        usuario = Usuario.query.filter_by(email=email_normalizado, ativo=True).first()
    except OperationalError as exc:
        db.session.rollback()
        raise BancoIndisponivelError("Falha temporaria de conexao com banco.") from exc

    if not usuario or not usuario.validar_senha(senha):
        return None

    return {
        "email": usuario.email,
        "papel": normalizar_papel(usuario.papel),
    }


def criar_usuario(email: str, senha: str, papel: str = "nao_editor") -> Usuario:
    email_normalizado = email.strip().lower()
    if not email_normalizado:
        raise ValueError("Email e obrigatorio")

    if not senha:
        raise ValueError("Senha e obrigatoria")

    existe = Usuario.query.filter_by(email=email_normalizado).first()
    if existe:
        raise ValueError("Ja existe usuario com esse email")

    usuario = Usuario(
        email=email_normalizado,
        papel=normalizar_papel(papel),
        ativo=True,
    )
    usuario.definir_senha(senha)
    db.session.add(usuario)
    db.session.commit()
    return usuario


def listar_usuarios() -> list[Usuario]:
    return Usuario.query.order_by(Usuario.email.asc()).all()


def carregar_usuario_por_id(usuario_id: int) -> Usuario | None:
    return Usuario.query.filter_by(id=usuario_id).first()


def atualizar_usuario(usuario_id: int, papel: str, senha: str | None = None) -> Usuario:
    usuario = carregar_usuario_por_id(usuario_id)
    if not usuario:
        raise ValueError("Usuario nao encontrado")

    usuario.papel = normalizar_papel(papel)

    if senha and senha.strip():
        usuario.definir_senha(senha.strip())

    db.session.commit()
    return usuario


def definir_usuario_ativo(usuario_id: int, ativo: bool) -> Usuario:
    usuario = carregar_usuario_por_id(usuario_id)
    if not usuario:
        raise ValueError("Usuario nao encontrado")

    usuario.ativo = bool(ativo)
    db.session.commit()
    return usuario


def bootstrap_admin_por_ambiente() -> None:
    email_admin = os.getenv("AUTH_USER_ADMIN_EMAIL", "").strip().lower()
    senha_admin = os.getenv("AUTH_USER_ADMIN_PASSWORD", "")
    papel_admin = normalizar_papel(os.getenv("AUTH_USER_ADMIN_PAPEL", "admin"))

    if not email_admin or not senha_admin:
        return

    try:
        _ = Usuario.query.filter_by(email=email_admin).one()
        return
    except NoResultFound:
        pass
    except (OperationalError, ProgrammingError):
        # O bootstrap nao deve quebrar quando a migration ainda nao foi aplicada.
        return

    usuario = Usuario(email=email_admin, papel=papel_admin, ativo=True)
    usuario.definir_senha(senha_admin)
    db.session.add(usuario)
    db.session.commit()


def registrar_sessao_usuario(email: str, papel: str) -> None:
    session["usuario_email"] = email
    session["papel_atual"] = normalizar_papel(papel)


def limpar_sessao_usuario() -> None:
    session.pop("usuario_email", None)
    session.pop("papel_atual", None)
