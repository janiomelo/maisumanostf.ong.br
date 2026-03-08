from flask import Blueprint, abort, redirect, render_template, request, url_for

from app.autorizacao import exigir_permissao
from app.domain.wiki import (
	atualizar_pagina_wiki,
	carregar_pagina_wiki,
	criar_pagina_wiki,
	listar_paginas_wiki,
	slugificar_titulo,
)

wiki_bp = Blueprint("wiki", __name__, url_prefix="/wiki")

@wiki_bp.get("/", strict_slashes=False)
def indice_wiki():
	paginas = listar_paginas_wiki()
	return render_template("wiki/indice.html", paginas=paginas)


@wiki_bp.get("/gestao")
@exigir_permissao("wiki", "editar")
def gestao_wiki():
	paginas = listar_paginas_wiki()
	return render_template("wiki/gestao.html", paginas=paginas)


@wiki_bp.get("/nova")
@exigir_permissao("wiki", "criar")
def nova_pagina_wiki():
	return render_template("wiki/nova-pagina.html", erro=None, valores={})


@wiki_bp.post("/nova")
@exigir_permissao("wiki", "criar")
def salvar_nova_pagina_wiki():
	titulo = request.form.get("titulo", "")
	conteudo_markdown = request.form.get("conteudo_markdown", "")
	slug = request.form.get("slug", "")

	if not slug.strip() and titulo.strip():
		slug = slugificar_titulo(titulo)

	try:
		nova_pagina = criar_pagina_wiki(slug, titulo, conteudo_markdown)
	except ValueError as exc:
		valores = {
			"slug": slug,
			"titulo": titulo,
			"conteudo_markdown": conteudo_markdown,
		}
		return render_template("wiki/nova-pagina.html", erro=str(exc), valores=valores), 400

	return redirect(url_for("wiki.pagina_wiki", slug=nova_pagina["slug"]))


@wiki_bp.get("/<slug>")
def pagina_wiki(slug: str):
	pagina = carregar_pagina_wiki(slug)
	if not pagina:
		abort(404)

	return render_template("wiki/pagina.html", pagina=pagina)


@wiki_bp.get("/<slug>/editar")
@exigir_permissao("wiki", "editar")
def editar_pagina_wiki(slug: str):
	pagina = carregar_pagina_wiki(slug)
	if not pagina:
		abort(404)

	return render_template("wiki/editar-pagina.html", pagina=pagina)


@wiki_bp.post("/<slug>/editar")
@exigir_permissao("wiki", "editar")
def salvar_pagina_wiki(slug: str):
	titulo = request.form.get("titulo", "")
	conteudo_markdown = request.form.get("conteudo_markdown", "")

	pagina_atualizada = atualizar_pagina_wiki(slug, titulo, conteudo_markdown)
	if not pagina_atualizada:
		pagina_atual = carregar_pagina_wiki(slug)
		if not pagina_atual:
			abort(404)

		erro = "Título e conteúdo são obrigatórios para salvar a página."
		return render_template("wiki/editar-pagina.html", pagina=pagina_atual, erro=erro), 400

	return redirect(url_for("wiki.pagina_wiki", slug=slug))
