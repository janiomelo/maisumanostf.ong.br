import os
from datetime import date, datetime

from flask import Blueprint, jsonify, make_response, render_template

main_bp = Blueprint("main", __name__)


def get_setting(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def parse_iso_date(raw: str, fallback: str) -> date:
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        return datetime.fromisoformat(fallback).date()


def year_fraction(value: date) -> float:
    start = date(value.year, 1, 1)
    end = date(value.year + 1, 1, 1)
    progress = (value - start).days
    total = (end - start).days
    return value.year + (progress / total)


def format_br(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def vacancy_dates() -> dict[str, date]:
    return {
        "fux": parse_iso_date(get_setting("VACANCY_FUX_DATE", "2028-04-26"), "2028-04-26"),
        "carmen": parse_iso_date(get_setting("VACANCY_CARMEN_DATE", "2029-04-19"), "2029-04-19"),
        "gilmar": parse_iso_date(get_setting("VACANCY_GILMAR_DATE", "2030-12-30"), "2030-12-30"),
    }


def build_chart_payload(vacancies: dict[str, date]) -> dict:
    current_year_marker = max(datetime.now().year, 2026)

    history_data = [
        {"x": 2000, "y": 1},
        {"x": 2006, "y": 2},
        {"x": 2011, "y": 2},
        {"x": 2023, "y": 2},
        {"x": current_year_marker, "y": 1},
    ]

    inertial_data = [
        {"x": current_year_marker, "y": 1},
        {"x": year_fraction(vacancies["carmen"]), "y": 0},
        {"x": 2032, "y": 0},
    ]

    campaign_data = [
        {"x": current_year_marker, "y": 1},
        {"x": year_fraction(vacancies["fux"]), "y": 2},
        {"x": year_fraction(vacancies["carmen"]), "y": 2},
        {"x": 2032, "y": 2},
    ]

    return {
        "xMin": 2000,
        "xMax": 2032,
        "yMin": 0,
        "yMax": 3,
        "datasets": [
            {"label": "Histórico (2000 até hoje)", "key": "history", "data": history_data},
            {"label": "Risco de extinção", "key": "inertia", "data": inertial_data},
            {
                "label": "Campanha Mais Uma (mínimo civilizatório)",
                "key": "campaign",
                "data": campaign_data,
            },
        ],
        "annotations": [
            {"x": current_year_marker, "y": 1, "text": "Hoje: Apenas 1 mulher"},
            {"x": year_fraction(vacancies["carmen"]), "y": 0, "text": "2029: Risco de Zero Ministras"},
            {"x": year_fraction(vacancies["fux"]), "y": 2, "text": "Meta: Igualar recorde com 2"},
        ],
    }


@main_bp.get("/")
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
        "home.html",
        countdown_target=target_raw,
        chart_payload=chart_payload,
        vacancy_labels=vacancy_labels,
    )

    response = make_response(html)
    response.headers["Cache-Control"] = "public, max-age=120, s-maxage=600, stale-while-revalidate=60"
    return response


@main_bp.get("/api/countdown")
def api_countdown():
    target_raw = get_setting("COUNTDOWN_TARGET", "2028-04-26T00:00:00-03:00")
    try:
        target_dt = datetime.fromisoformat(target_raw)
    except ValueError:
        target_dt = datetime.fromisoformat("2028-04-26T00:00:00-03:00")
    return jsonify({"target": target_dt.isoformat()})