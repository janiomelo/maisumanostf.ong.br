from datetime import date, datetime

import pytest

from app import main


@pytest.mark.unit
def test_get_setting_retorna_default_quando_ausente(monkeypatch):
    monkeypatch.delenv("CHAVE_INEXISTENTE", raising=False)
    assert main.get_setting("CHAVE_INEXISTENTE", "padrao") == "padrao"


@pytest.mark.unit
def test_get_setting_retorna_valor_do_ambiente(monkeypatch):
    monkeypatch.setenv("CHAVE_TESTE", "valor")
    assert main.get_setting("CHAVE_TESTE", "padrao") == "valor"


@pytest.mark.unit
def test_parse_iso_date_valida_e_fallback():
    assert main.parse_iso_date("2028-04-26", "2027-01-01") == date(2028, 4, 26)
    assert main.parse_iso_date("invalida", "2027-01-01") == date(2027, 1, 1)


@pytest.mark.unit
def test_year_fraction_no_inicio_do_ano():
    assert main.year_fraction(date(2026, 1, 1)) == pytest.approx(2026.0)


@pytest.mark.unit
def test_year_fraction_no_fim_do_ano():
    valor = main.year_fraction(date(2026, 12, 31))
    assert 2027.0 > valor > 2026.9


@pytest.mark.unit
def test_format_br():
    assert main.format_br(date(2028, 4, 26)) == "26/04/2028"


@pytest.mark.unit
def test_vacancy_dates_ler_variaveis(monkeypatch):
    monkeypatch.setenv("VACANCY_FUX_DATE", "2031-01-10")
    monkeypatch.setenv("VACANCY_CARMEN_DATE", "2032-02-11")
    monkeypatch.setenv("VACANCY_GILMAR_DATE", "2033-03-12")

    vagas = main.vacancy_dates()

    assert vagas["fux"] == date(2031, 1, 10)
    assert vagas["carmen"] == date(2032, 2, 11)
    assert vagas["gilmar"] == date(2033, 3, 12)


@pytest.mark.unit
def test_vacancy_dates_fallback_em_data_invalida(monkeypatch):
    monkeypatch.setenv("VACANCY_FUX_DATE", "nao-data")

    vagas = main.vacancy_dates()

    assert vagas["fux"] == date(2028, 4, 26)


@pytest.mark.unit
def test_build_chart_payload_estrutura(monkeypatch):
    class FakeDateTime(datetime):
        @classmethod
        def now(cls):
            return cls(2027, 5, 20)

    monkeypatch.setattr(main, "datetime", FakeDateTime)

    payload = main.build_chart_payload(
        {
            "fux": date(2028, 4, 26),
            "carmen": date(2029, 4, 19),
            "gilmar": date(2030, 12, 30),
        }
    )

    assert payload["xMin"] == 2000
    assert payload["xMax"] == 2032
    assert payload["yMin"] == 0
    assert payload["yMax"] == 3
    assert len(payload["datasets"]) == 3
    assert {item["key"] for item in payload["datasets"]} == {"history", "inertia", "campaign"}
    assert len(payload["annotations"]) == 3


@pytest.mark.unit
def test_build_countdown_target_com_valor_valido(monkeypatch):
    monkeypatch.setenv("COUNTDOWN_TARGET", "2031-01-10T09:00:00-03:00")
    assert main._build_countdown_target() == "2031-01-10T09:00:00-03:00"


@pytest.mark.unit
def test_build_countdown_target_com_fallback(monkeypatch):
    monkeypatch.setenv("COUNTDOWN_TARGET", "valor-invalido")
    assert main._build_countdown_target() == "2028-04-26T00:00:00-03:00"
