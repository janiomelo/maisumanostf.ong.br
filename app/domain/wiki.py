import re
import unicodedata

from app.dados import WikiPagina, db

_SLUG_REGEX = re.compile(r"^[a-z0-9-]+$")


def _is_slug_valido(slug: str) -> bool:
    return bool(_SLUG_REGEX.fullmatch(slug))


def slugificar_titulo(texto: str) -> str:
    texto_normalizado = unicodedata.normalize("NFKD", texto or "")
    sem_acentos = "".join(char for char in texto_normalizado if not unicodedata.combining(char))
    minusculo = sem_acentos.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", minusculo)
    return slug.strip("-")


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


def criar_pagina_wiki(slug: str, titulo: str, conteudo_markdown: str) -> dict:
    slug_limpo = (slug or "").strip().lower()
    titulo_limpo = (titulo or "").strip()
    conteudo_limpo = (conteudo_markdown or "").strip()

    if not titulo_limpo or not conteudo_limpo:
        raise ValueError("Titulo e conteudo sao obrigatorios para criar a pagina.")

    if not slug_limpo:
        slug_limpo = slugificar_titulo(titulo_limpo)

    if not _is_slug_valido(slug_limpo):
        raise ValueError("Slug invalido. Use apenas letras minusculas, numeros e hifen.")

    existe = WikiPagina.query.filter_by(slug=slug_limpo).first()
    if existe:
        raise ValueError("Ja existe uma pagina com este slug.")

    pagina = WikiPagina(
        slug=slug_limpo,
        titulo=titulo_limpo,
        conteudo_markdown=conteudo_limpo,
    )
    db.session.add(pagina)
    db.session.commit()

    pagina_dict = carregar_pagina_wiki(slug_limpo)
    if not pagina_dict:
        raise ValueError("Falha ao carregar pagina apos criacao.")

    return pagina_dict
