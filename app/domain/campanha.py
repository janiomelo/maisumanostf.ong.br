import os
from datetime import date, datetime


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


def build_countdown_target() -> str:
    target_raw = get_setting("COUNTDOWN_TARGET", "2028-04-26T00:00:00-03:00")
    try:
        target_dt = datetime.fromisoformat(target_raw)
    except ValueError:
        target_dt = datetime.fromisoformat("2028-04-26T00:00:00-03:00")
    return target_dt.isoformat()


def build_countdown_initial_state(target_iso: str, now: datetime | None = None) -> dict[str, str]:
    try:
        target_dt = datetime.fromisoformat(target_iso)
    except ValueError:
        target_dt = datetime.fromisoformat("2028-04-26T00:00:00-03:00")

    if now is None:
        if target_dt.tzinfo is not None:
            now = datetime.now(target_dt.tzinfo)
        else:
            now = datetime.now()

    diff_total = int((target_dt - now).total_seconds())
    if diff_total < 0:
        diff_total = 0

    days = diff_total // 86400
    diff_total -= days * 86400
    hours = diff_total // 3600
    diff_total -= hours * 3600
    minutes = diff_total // 60
    seconds = diff_total - (minutes * 60)

    return {
        "days": str(days),
        "hours": str(hours).zfill(2),
        "minutes": str(minutes).zfill(2),
        "seconds": str(seconds).zfill(2),
    }
