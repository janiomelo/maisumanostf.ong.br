from flask import Blueprint, current_app, jsonify, make_response, render_template, request, url_for
from sqlalchemy.exc import OperationalError

from app.dados.modelos import WikiPagina
from app.domain.campanha import (
    build_chart_payload,
    build_countdown_target,
    format_br,
    get_setting,
    vacancy_dates,
)
from app.domain.paginas_gerais import carregar_links_paginas_gerais

publico_bp = Blueprint("main", __name__)


@publico_bp.app_context_processor
def injetar_paginas_gerais() -> dict[str, object]:
    return {
        "paginas_gerais_links": carregar_links_paginas_gerais(),
    }


@publico_bp.get("/")
def home():
    vacancies = vacancy_dates()
    default_target = f"{vacancies['fux'].isoformat()}T00:00:00-03:00"
    target_raw = get_setting("COUNTDOWN_TARGET", default_target)
    chart_payload = build_chart_payload(vacancies)
    vacancy_labels = {
        "fux": format_br(vacancies["fux"]),
        "carmen": format_br(vacancies["carmen"]),
        "gilmar": format_br(vacancies["gilmar"]),
    }

    html = render_template(
        "publico/home.html",
        countdown_target=target_raw,
        chart_payload=chart_payload,
        vacancy_labels=vacancy_labels,
    )

    response = make_response(html)
    response.headers["Cache-Control"] = "public, max-age=120, s-maxage=600, stale-while-revalidate=60"
    return response


@publico_bp.get("/api/contagem-regressiva")
def api_contagem_regressiva():
    response = jsonify({"alvo": build_countdown_target()})
    response.headers["Content-Language"] = "pt-BR"
    return response


@publico_bp.get("/api/countdown")
def api_countdown_legado():
    alvo = build_countdown_target()
    response = jsonify(
        {
            "alvo": alvo,
            "target": alvo,
            "aviso": "Use /api/contagem-regressiva; este endpoint legado sera removido.",
        }
    )
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = '</api/contagem-regressiva>; rel="successor-version"'
    response.headers["Content-Language"] = "pt-BR"
    return response


@publico_bp.get("/robots.txt")
def robots_txt():
    sitemap_url = url_for("main.sitemap_xml", _external=True)
    conteudo = f"User-agent: *\nAllow: /\nSitemap: {sitemap_url}\n"
    response = make_response(conteudo)
    response.mimetype = "text/plain"
    return response


@publico_bp.get("/sitemap.xml")
def sitemap_xml():
    paginas_wiki: list[str] = []
    extras_configurados: list[str] = []

    try:
        paginas_wiki = [
            url_for("wiki.pagina_wiki", slug=pagina.slug, _external=True)
            for pagina in WikiPagina.query.order_by(WikiPagina.slug.asc()).all()
        ]

        paginas_gerais = carregar_links_paginas_gerais()
        extras_configurados = [
            url_for("wiki.pagina_wiki", slug=item["slug"], _external=True)
            for item in paginas_gerais.values()
            if item is not None
        ]
    except OperationalError as exc:
        current_app.logger.warning("Falha ao consultar banco para sitemap.xml. Mantendo URLs públicas básicas: %s", exc)

    paginas = [
        url_for("main.home", _external=True),
        url_for("wiki.indice_wiki", _external=True),
        url_for("apoios.assinar_manifesto", _external=True),
        url_for("autenticacao.entrar", _external=True),
        *extras_configurados,
        *paginas_wiki,
    ]
    paginas = list(dict.fromkeys(paginas))

    linhas = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for pagina in paginas:
        linhas.extend(
            [
                "  <url>",
                f"    <loc>{pagina}</loc>",
                "  </url>",
            ]
        )
    linhas.append("</urlset>")

    response = make_response("\n".join(linhas))
    response.mimetype = "application/xml"
    return response
