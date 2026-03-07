import re

from app.dados import WikiPagina, db

_SLUG_REGEX = re.compile(r"^[a-z0-9-]+$")


def _is_slug_valido(slug: str) -> bool:
    return bool(_SLUG_REGEX.fullmatch(slug))


def _parse_conteudo_markdown(raw: str) -> tuple[str, list[dict[str, str]]]:
    linhas = [item.rstrip() for item in raw.splitlines()]
    titulo = ""
    blocos: list[dict[str, str]] = []

    for linha in linhas:
        if not linha.strip():
            continue

        if linha.startswith("# ") and not titulo:
            titulo = linha[2:].strip()
            continue

        if linha.startswith("## "):
            blocos.append({"tipo": "h2", "texto": linha[3:].strip()})
            continue

        blocos.append({"tipo": "p", "texto": linha.strip()})

    if not titulo:
        titulo = "Pagina Wiki"

    return titulo, blocos


def listar_paginas_wiki() -> list[dict[str, str]]:
    paginas_db = WikiPagina.query.order_by(WikiPagina.slug.asc()).all()

    paginas: list[dict[str, str]] = []
    for item in paginas_db:
        titulo, blocos = _parse_conteudo_markdown(item.conteudo_markdown)
        resumo = next((item["texto"] for item in blocos if item["tipo"] == "p"), "Sem resumo.")
        paginas.append({"slug": item.slug, "titulo": item.titulo or titulo, "resumo": resumo})

    return paginas


def carregar_pagina_wiki(slug: str) -> dict | None:
    if not _is_slug_valido(slug):
        return None

    pagina = WikiPagina.query.filter_by(slug=slug).first()
    if not pagina:
        return None

    titulo, blocos = _parse_conteudo_markdown(pagina.conteudo_markdown)
    return {
        "slug": pagina.slug,
        "titulo": pagina.titulo or titulo,
        "blocos": blocos,
        "conteudo_markdown": pagina.conteudo_markdown,
    }


def atualizar_pagina_wiki(slug: str, titulo: str, conteudo_markdown: str) -> dict | None:
    if not _is_slug_valido(slug):
        return None

    pagina = WikiPagina.query.filter_by(slug=slug).first()
    if not pagina:
        return None

    titulo_limpo = (titulo or "").strip()
    conteudo_limpo = (conteudo_markdown or "").strip()
    if not titulo_limpo or not conteudo_limpo:
        return None

    pagina.titulo = titulo_limpo
    pagina.conteudo_markdown = conteudo_limpo
    db.session.commit()

    return carregar_pagina_wiki(slug)
