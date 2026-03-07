from flask import Blueprint, abort, g, redirect, render_template, request, url_for

from app.autorizacao import exigir_permissao, normalizar_papel
from app.domain.wiki import atualizar_pagina_wiki, carregar_pagina_wiki, listar_paginas_wiki

wiki_bp = Blueprint("wiki", __name__, url_prefix="/wiki")


@wiki_bp.before_request
def carregar_contexto_de_papel() -> None:
	# Cabecalho temporario para preparar o fluxo de permissao ate entrar autenticacao real.
	g.papel_atual = normalizar_papel(request.headers.get("X-Papel-Usuario"))


@wiki_bp.get("/", strict_slashes=False)
def indice_wiki():
	paginas = listar_paginas_wiki()
	return render_template("wiki/indice.html", paginas=paginas)


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

		erro = "Titulo e conteudo sao obrigatorios para salvar a pagina."
		return render_template("wiki/editar-pagina.html", pagina=pagina_atual, erro=erro), 400

	return redirect(url_for("wiki.pagina_wiki", slug=slug))
