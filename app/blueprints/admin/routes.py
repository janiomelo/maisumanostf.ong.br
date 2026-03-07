from flask import Blueprint, abort, g, redirect, render_template, request, url_for

from app.autenticacao import (
	atualizar_usuario,
	criar_usuario,
	definir_usuario_ativo,
	listar_usuarios,
)
from app.autorizacao import PAPEIS_VALIDOS, exigir_permissao

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/usuarios")
@exigir_permissao("admin", "gerenciar")
def listar_usuarios_admin():
	usuarios = listar_usuarios()
	return render_template(
		"admin/usuarios.html",
		usuarios=usuarios,
		papeis_validos=PAPEIS_VALIDOS,
		erro=None,
	)


@admin_bp.post("/usuarios")
@exigir_permissao("admin", "gerenciar")
def criar_usuario_admin():
	email = request.form.get("email", "")
	senha = request.form.get("senha", "")
	papel = request.form.get("papel", "nao_editor")

	try:
		criar_usuario(email=email, senha=senha, papel=papel)
	except ValueError as exc:
		usuarios = listar_usuarios()
		return render_template(
			"admin/usuarios.html",
			usuarios=usuarios,
			papeis_validos=PAPEIS_VALIDOS,
			erro=str(exc),
		), 400

	return redirect(url_for("admin.listar_usuarios_admin"))


@admin_bp.post("/usuarios/<int:usuario_id>/atualizar")
@exigir_permissao("admin", "gerenciar")
def atualizar_usuario_admin(usuario_id: int):
	papel = request.form.get("papel", "nao_editor")
	senha = request.form.get("senha", "")

	try:
		usuario = atualizar_usuario(usuario_id=usuario_id, papel=papel, senha=senha)
	except ValueError:
		abort(404)

	if usuario.email == getattr(g, "usuario_email", None) and usuario.papel != "admin":
		atualizar_usuario(usuario_id=usuario_id, papel="admin", senha="")
		usuarios = listar_usuarios()
		erro = "Nao e permitido remover seu proprio papel de admin."
		return render_template(
			"admin/usuarios.html",
			usuarios=usuarios,
			papeis_validos=PAPEIS_VALIDOS,
			erro=erro,
		), 400

	return redirect(url_for("admin.listar_usuarios_admin"))


@admin_bp.post("/usuarios/<int:usuario_id>/desativar")
@exigir_permissao("admin", "gerenciar")
def desativar_usuario_admin(usuario_id: int):
	try:
		usuario = definir_usuario_ativo(usuario_id=usuario_id, ativo=False)
	except ValueError:
		abort(404)

	if usuario.email == getattr(g, "usuario_email", None):
		definir_usuario_ativo(usuario_id=usuario_id, ativo=True)
		usuarios = listar_usuarios()
		erro = "Nao e permitido desativar seu proprio usuario admin."
		return render_template(
			"admin/usuarios.html",
			usuarios=usuarios,
			papeis_validos=PAPEIS_VALIDOS,
			erro=erro,
		), 400

	return redirect(url_for("admin.listar_usuarios_admin"))


@admin_bp.post("/usuarios/<int:usuario_id>/ativar")
@exigir_permissao("admin", "gerenciar")
def ativar_usuario_admin(usuario_id: int):
	try:
		definir_usuario_ativo(usuario_id=usuario_id, ativo=True)
	except ValueError:
		abort(404)

	return redirect(url_for("admin.listar_usuarios_admin"))
