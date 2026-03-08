import re

import pytest


@pytest.mark.e2e
def test_fluxo_publico_completo_home_para_apis(client, monkeypatch):
    monkeypatch.setenv("COUNTDOWN_TARGET", "2031-09-01T08:00:00-03:00")

    home_response = client.get("/")
    assert home_response.status_code == 200
    home_html = home_response.get_data(as_text=True)

    match = re.search(r'data-alvo="([^"]+)"', home_html)
    assert match is not None
    alvo_na_home = match.group(1)
    assert alvo_na_home == "2031-09-01T08:00:00-03:00"

    api_nova = client.get("/api/contagem-regressiva")
    assert api_nova.status_code == 200
    assert api_nova.json["alvo"] == alvo_na_home

    api_legada = client.get("/api/countdown")
    assert api_legada.status_code == 200
    assert api_legada.json["alvo"] == alvo_na_home
    assert api_legada.json["target"] == alvo_na_home
    assert api_legada.headers.get("Deprecation") == "true"
    assert "successor-version" in api_legada.headers.get("Link", "")


@pytest.mark.e2e
def test_fluxo_de_navegacao_possui_ancoras_essenciais(client):
    response = client.get("/")
    assert response.status_code == 200

    html = response.get_data(as_text=True)
    for ancora in ["#manifesto", "#dados", "#sobre"]:
        assert ancora in html
