from flask import Blueprint, jsonify, make_response, render_template

from app.domain.campanha import (
    build_chart_payload,
    build_countdown_target,
    format_br,
    get_setting,
    vacancy_dates,
)

publico_bp = Blueprint("main", __name__)


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
    conteudo = "User-agent: *\nAllow: /\n"
    response = make_response(conteudo)
    response.mimetype = "text/plain"
    return response
