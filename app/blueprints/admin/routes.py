from flask import Blueprint, abort, g, redirect, render_template, request, url_for

from app.apoios import listar_apoios_admin, remover_apoio_admin
from app.autenticacao import (
	atualizar_usuario,
	criar_usuario,
	definir_usuario_ativo,
	listar_usuarios,
)
from app.autorizacao import PAPEIS_VALIDOS, exigir_permissao
from app.paginas_gerais import (
	CHAVE_WIKI_ESTATUTO,
	CHAVE_WIKI_POLITICA_PRIVACIDADE,
	CHAVE_WIKI_TERMOS_USO,
	atualizar_configuracoes_paginas_gerais,
	carregar_configuracoes_paginas_gerais,
)
from app.dados.modelos import WikiPagina

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _filtros_apoios_da_requisicao() -> dict[str, str | int]:
	termo = request.values.get("termo", "").strip()
	data_inicial = request.values.get("data_inicial", "").strip()
	data_final = request.values.get("data_final", "").strip()

	try:
		pagina = int(request.values.get("pagina", "1"))
	except ValueError:
		pagina = 1

	try:
		por_pagina = int(request.values.get("por_pagina", "20"))
	except ValueError:
		por_pagina = 20

	return {
		"termo": termo,
		"data_inicial": data_inicial,
		"data_final": data_final,
		"pagina": pagina,
		"por_pagina": por_pagina,
	}


@admin_bp.get("/usuarios")
@exigir_permissao("admin", "gerenciar")
def listar_usuarios_admin():
	usuarios = listar_usuarios()
	return render_template(
		"admin/usuarios.html",
		aba_admin_ativa="usuarios",
		usuarios=usuarios,
		papeis_validos=PAPEIS_VALIDOS,
		erro=None,
	)


@admin_bp.get("")
@exigir_permissao("admin", "gerenciar")
def painel_admin():
	return render_template("admin/painel.html", aba_admin_ativa="painel")


@admin_bp.get("/paginas-gerais")
@exigir_permissao("admin", "gerenciar")
def paginas_gerais_admin():
	config = carregar_configuracoes_paginas_gerais()
	paginas_wiki = WikiPagina.query.order_by(WikiPagina.slug.asc()).all()
	return render_template(
		"admin/paginas-gerais.html",
		aba_admin_ativa="paginas-gerais",
		erro=None,
		sucesso=None,
		paginas_wiki=paginas_wiki,
		chave_estatuto=CHAVE_WIKI_ESTATUTO,
		chave_politica=CHAVE_WIKI_POLITICA_PRIVACIDADE,
		chave_termos=CHAVE_WIKI_TERMOS_USO,
		config=config,
	)


@admin_bp.post("/paginas-gerais")
@exigir_permissao("admin", "gerenciar")
def salvar_paginas_gerais_admin():
	estatuto_slug = request.form.get(CHAVE_WIKI_ESTATUTO, "")
	politica_slug = request.form.get(CHAVE_WIKI_POLITICA_PRIVACIDADE, "")
	termos_slug = request.form.get(CHAVE_WIKI_TERMOS_USO, "")

	try:
		atualizar_configuracoes_paginas_gerais(
			estatuto_slug=estatuto_slug,
			politica_slug=politica_slug,
			termos_slug=termos_slug,
		)
	except ValueError as exc:
		config = carregar_configuracoes_paginas_gerais()
		paginas_wiki = WikiPagina.query.order_by(WikiPagina.slug.asc()).all()
		return render_template(
			"admin/paginas-gerais.html",
			aba_admin_ativa="paginas-gerais",
			erro=str(exc),
			sucesso=None,
			paginas_wiki=paginas_wiki,
			chave_estatuto=CHAVE_WIKI_ESTATUTO,
			chave_politica=CHAVE_WIKI_POLITICA_PRIVACIDADE,
			chave_termos=CHAVE_WIKI_TERMOS_USO,
			config=config,
		), 400

	return redirect(url_for("admin.paginas_gerais_admin"))


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
			aba_admin_ativa="usuarios",
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
		erro = "Não é permitido remover seu próprio papel de admin."
		return render_template(
			"admin/usuarios.html",
			aba_admin_ativa="usuarios",
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
		erro = "Não é permitido desativar seu próprio usuário admin."
		return render_template(
			"admin/usuarios.html",
			aba_admin_ativa="usuarios",
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


@admin_bp.get("/apoios")
@exigir_permissao("admin", "gerenciar")
def listar_apoios_admin_route():
	filtros = _filtros_apoios_da_requisicao()
	resultado = listar_apoios_admin(
		termo=str(filtros["termo"]),
		data_inicial=str(filtros["data_inicial"]),
		data_final=str(filtros["data_final"]),
		pagina=int(filtros["pagina"]),
		por_pagina=int(filtros["por_pagina"]),
	)

	return render_template(
		"admin/apoios.html",
		aba_admin_ativa="apoios",
		apoios=resultado.apoios,
		total_geral=resultado.total_geral,
		total_filtrado=resultado.total_filtrado,
		pagina=resultado.pagina,
		por_pagina=resultado.por_pagina,
		total_paginas=resultado.total_paginas,
		termo=str(filtros["termo"]),
		data_inicial=str(filtros["data_inicial"]),
		data_final=str(filtros["data_final"]),
	)


@admin_bp.post("/apoios/<int:apoio_id>/remover")
@exigir_permissao("admin", "gerenciar")
def remover_apoio_admin_route(apoio_id: int):
	filtros = _filtros_apoios_da_requisicao()
	removido = remover_apoio_admin(apoio_id)
	if not removido:
		abort(404)

	return redirect(
		url_for(
			"admin.listar_apoios_admin_route",
			termo=filtros["termo"],
			data_inicial=filtros["data_inicial"],
			data_final=filtros["data_final"],
			pagina=filtros["pagina"],
			por_pagina=filtros["por_pagina"],
		)
	)
