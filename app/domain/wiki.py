import re
import unicodedata
from html import escape
from urllib.parse import urlparse

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
        titulo = "Página Wiki"

    return titulo, blocos


def _url_markdown_valida(url: str) -> bool:
    url_limpa = url.strip()
    if url_limpa.startswith("/"):
        return True

    parsed = urlparse(url_limpa)
    return parsed.scheme in {"http", "https", "mailto"}


def _render_inline_markdown(texto: str) -> str:
    escaped = escape(texto)

    def repl_link(match: re.Match[str]) -> str:
        label = match.group(1)
        url = match.group(2).strip()
        if not _url_markdown_valida(url):
            return escape(match.group(0))

        return f'<a href="{escape(url, quote=True)}" rel="noopener">{label}</a>'

    escaped = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", repl_link, escaped)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return escaped


def _render_markdown_html(raw: str) -> str:
    linhas = [item.rstrip("\n") for item in raw.splitlines()]
    html: list[str] = []
    i = 0
    pulou_titulo_h1 = False

    while i < len(linhas):
        linha = linhas[i].rstrip()
        linha_stripped = linha.strip()

        if not linha_stripped:
            i += 1
            continue

        if linha_stripped.startswith("# ") and not pulou_titulo_h1:
            pulou_titulo_h1 = True
            i += 1
            continue

        if linha_stripped.startswith("```"):
            i += 1
            buffer_codigo: list[str] = []
            while i < len(linhas) and not linhas[i].strip().startswith("```"):
                buffer_codigo.append(linhas[i])
                i += 1
            if i < len(linhas):
                i += 1
            html.append(f"<pre><code>{escape(chr(10).join(buffer_codigo))}</code></pre>")
            continue

        if linha_stripped.startswith("### "):
            html.append(f"<h3>{_render_inline_markdown(linha_stripped[4:].strip())}</h3>")
            i += 1
            continue

        if linha_stripped.startswith("## "):
            html.append(f"<h2>{_render_inline_markdown(linha_stripped[3:].strip())}</h2>")
            i += 1
            continue

        if re.match(r"^[-*+]\s+", linha_stripped):
            itens: list[str] = []
            while i < len(linhas) and re.match(r"^[-*+]\s+", linhas[i].strip()):
                item = re.sub(r"^[-*+]\s+", "", linhas[i].strip())
                itens.append(f"<li>{_render_inline_markdown(item)}</li>")
                i += 1
            html.append("<ul>" + "".join(itens) + "</ul>")
            continue

        if re.match(r"^\d+\.\s+", linha_stripped):
            itens: list[str] = []
            while i < len(linhas) and re.match(r"^\d+\.\s+", linhas[i].strip()):
                item = re.sub(r"^\d+\.\s+", "", linhas[i].strip())
                itens.append(f"<li>{_render_inline_markdown(item)}</li>")
                i += 1
            html.append("<ol>" + "".join(itens) + "</ol>")
            continue

        buffer_paragrafo = [linha_stripped]
        i += 1
        while i < len(linhas):
            prox = linhas[i].strip()
            if not prox:
                i += 1
                break
            if prox.startswith(("## ", "### ", "```")):
                break
            if re.match(r"^[-*+]\s+", prox) or re.match(r"^\d+\.\s+", prox):
                break
            buffer_paragrafo.append(prox)
            i += 1

        texto = " ".join(buffer_paragrafo)
        html.append(f"<p>{_render_inline_markdown(texto)}</p>")

    return "\n".join(html)


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
        "conteudo_html": _render_markdown_html(pagina.conteudo_markdown),
        "conteudo_markdown": pagina.conteudo_markdown,
        "criado_em": pagina.criado_em,
        "atualizado_em": pagina.atualizado_em,
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
        raise ValueError("Título e conteúdo são obrigatórios para criar a página.")

    if not slug_limpo:
        slug_limpo = slugificar_titulo(titulo_limpo)

    if not _is_slug_valido(slug_limpo):
        raise ValueError("Slug inválido. Use apenas letras minúsculas, números e hífen.")

    existe = WikiPagina.query.filter_by(slug=slug_limpo).first()
    if existe:
        raise ValueError("Já existe uma página com este slug.")

    pagina = WikiPagina(
        slug=slug_limpo,
        titulo=titulo_limpo,
        conteudo_markdown=conteudo_limpo,
    )
    db.session.add(pagina)
    db.session.commit()

    pagina_dict = carregar_pagina_wiki(slug_limpo)
    if not pagina_dict:
        raise ValueError("Falha ao carregar página após criação.")

    return pagina_dict
