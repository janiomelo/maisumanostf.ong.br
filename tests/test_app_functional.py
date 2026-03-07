import re

import pytest

from app import create_app


@pytest.mark.functional
def test_create_app_registra_rotas_principais():
    app = create_app()
    rotas = {rule.rule for rule in app.url_map.iter_rules()}

    assert "/" in rotas
    assert "/api/contagem-regressiva" in rotas
    assert "/api/countdown" in rotas
    assert "/wiki/" in rotas
    assert "/wiki/<slug>" in rotas
    assert "/wiki/<slug>/editar" in rotas


@pytest.mark.functional
def test_home_renderiza_conteudo_essencial(client):
    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Representatividade Feminina no STF" in html
    assert "data-alvo=" in html
    assert "id=\"manifesto\"" in html
    assert "id=\"dados\"" in html
    assert "id=\"participe\"" in html
    assert "id=\"transparencia\"" in html
    assert "chart.umd.min.js" in html

    cache_control = response.headers.get("Cache-Control", "")
    assert "max-age=120" in cache_control
    assert "s-maxage=600" in cache_control


@pytest.mark.functional
def test_api_contagem_regressiva_retorna_alvo(client, monkeypatch):
    monkeypatch.setenv("COUNTDOWN_TARGET", "2032-03-04T10:20:30-03:00")

    response = client.get("/api/contagem-regressiva")

    assert response.status_code == 200
    assert response.is_json
    assert response.json == {"alvo": "2032-03-04T10:20:30-03:00"}
    assert response.headers.get("Content-Language") == "pt-BR"


@pytest.mark.functional
def test_api_contagem_regressiva_fallback_quando_invalida(client, monkeypatch):
    monkeypatch.setenv("COUNTDOWN_TARGET", "nao-iso")

    response = client.get("/api/contagem-regressiva")

    assert response.status_code == 200
    assert response.json == {"alvo": "2028-04-26T00:00:00-03:00"}


@pytest.mark.functional
def test_api_countdown_legado_tem_headers_e_campos(client, monkeypatch):
    monkeypatch.setenv("COUNTDOWN_TARGET", "2035-06-01T00:00:00-03:00")

    response = client.get("/api/countdown")

    assert response.status_code == 200
    assert response.is_json
    assert response.json["alvo"] == "2035-06-01T00:00:00-03:00"
    assert response.json["target"] == "2035-06-01T00:00:00-03:00"
    assert "legacy" not in response.json
    assert "legado" in response.json["aviso"].lower()
    assert response.headers.get("Deprecation") == "true"
    assert response.headers.get("Content-Language") == "pt-BR"
    assert "rel=\"successor-version\"" in response.headers.get("Link", "")


@pytest.mark.functional
def test_static_main_js_disponivel(client):
    response = client.get("/static/main.js")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "function startCountdown()" in body
    assert "dataset.alvo" in body


@pytest.mark.functional
def test_home_data_alvo_corresponde_ao_valor_configurado(client, monkeypatch):
    monkeypatch.setenv("COUNTDOWN_TARGET", "2030-11-12T13:14:15-03:00")

    response = client.get("/")
    html = response.get_data(as_text=True)

    match = re.search(r'data-alvo="([^"]+)"', html)
    assert match is not None
    assert match.group(1) == "2030-11-12T13:14:15-03:00"


@pytest.mark.functional
def test_wiki_indice_publica(client):
    response = client.get("/wiki/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Wiki da Campanha" in html
    assert "Estatuto Basico Ampliado" in html
    assert "/wiki/estatuto-basico-ampliado" in html


@pytest.mark.functional
def test_wiki_sem_barra_final_nao_redireciona(client):
    response = client.get("/wiki")
    assert response.status_code == 200


@pytest.mark.functional
def test_wiki_estatuto_publico(client):
    response = client.get("/wiki/estatuto-basico-ampliado")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Estatuto Basico Ampliado" in html
    assert "Escopo inicial" in html


@pytest.mark.functional
def test_wiki_edicao_exige_papel_editor(client):
    sem_permissao = client.get("/wiki/estatuto-basico-ampliado/editar")
    assert sem_permissao.status_code == 403

    com_permissao = client.get(
        "/wiki/estatuto-basico-ampliado/editar",
        headers={"X-Papel-Usuario": "editor"},
    )
    assert com_permissao.status_code == 200


@pytest.mark.functional
def test_wiki_edicao_persistida_no_banco(client):
    response = client.post(
        "/wiki/estatuto-basico-ampliado/editar",
        headers={"X-Papel-Usuario": "editor"},
        data={
            "titulo": "Estatuto Basico Ampliado (Atualizado)",
            "conteudo_markdown": "# Estatuto Basico Ampliado (Atualizado)\n\nTexto editado via teste.",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Estatuto Basico Ampliado (Atualizado)" in html
    assert "Texto editado via teste." in html


@pytest.mark.functional
def test_wiki_post_edicao_sem_papel_editor_retorna_403(client):
    response = client.post(
        "/wiki/estatuto-basico-ampliado/editar",
        data={
            "titulo": "Tentativa sem permissao",
            "conteudo_markdown": "# Tentativa\n\nSem permissao.",
        },
    )
    assert response.status_code == 403


@pytest.mark.functional
def test_wiki_post_edicao_com_payload_invalido_retorna_400(client):
    response = client.post(
        "/wiki/estatuto-basico-ampliado/editar",
        headers={"X-Papel-Usuario": "editor"},
        data={
            "titulo": "",
            "conteudo_markdown": "",
        },
    )
    assert response.status_code == 400


@pytest.mark.functional
def test_wiki_retorna_404_para_slug_inexistente(client):
    response = client.get("/wiki/pagina-inexistente")
    assert response.status_code == 404
