"""Compatibilidade temporaria para imports legados de app.main."""

from app.blueprints.publico.routes import publico_bp as main_bp
from app.domain.campanha import (
    build_chart_payload,
    build_countdown_target as _build_countdown_target,
    format_br,
    get_setting,
    parse_iso_date,
    vacancy_dates,
    year_fraction,
)

__all__ = [
    "main_bp",
    "get_setting",
    "parse_iso_date",
    "year_fraction",
    "format_br",
    "vacancy_dates",
    "build_chart_payload",
    "_build_countdown_target",
]