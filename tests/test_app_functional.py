import re

import pytest

from app import create_app
from app.dados.modelos import Usuario


@pytest.mark.functional
def test_create_app_registra_rotas_principais():
    app = create_app()
    rotas = {rule.rule for rule in app.url_map.iter_rules()}

    assert "/" in rotas
    assert "/api/contagem-regressiva" in rotas
    assert "/api/countdown" in rotas
    assert "/entrar" in rotas
    assert "/sair" in rotas
    assert "/wiki/" in rotas
    assert "/wiki/gestao" in rotas
    assert "/wiki/nova" in rotas
    assert "/wiki/<slug>" in rotas
    assert "/wiki/<slug>/editar" in rotas
    assert "/admin/usuarios" in rotas
    assert "/admin/usuarios/<int:usuario_id>/atualizar" in rotas
    assert "/admin/usuarios/<int:usuario_id>/desativar" in rotas
    assert "/admin/usuarios/<int:usuario_id>/ativar" in rotas


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
def test_wiki_edicao_exige_autenticacao(client):
    sem_permissao = client.get("/wiki/estatuto-basico-ampliado/editar")
    assert sem_permissao.status_code == 302
    assert "/entrar?proximo=/wiki/estatuto-basico-ampliado/editar" in sem_permissao.headers["Location"]


@pytest.mark.functional
def test_wiki_edicao_exige_papel_editor(client):
    client.post(
        "/entrar",
        data={"email": "editor@teste.local", "senha": "123456"},
    )

    com_permissao = client.get("/wiki/estatuto-basico-ampliado/editar")
    assert com_permissao.status_code == 200


@pytest.mark.functional
def test_wiki_edicao_persistida_no_banco(client):
    client.post(
        "/entrar",
        data={"email": "editor@teste.local", "senha": "123456"},
    )

    response = client.post(
        "/wiki/estatuto-basico-ampliado/editar",
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
    assert response.status_code == 302
    assert "/entrar?proximo=/wiki/estatuto-basico-ampliado/editar" in response.headers["Location"]


@pytest.mark.functional
def test_wiki_post_edicao_com_payload_invalido_retorna_400(client):
    client.post(
        "/entrar",
        data={"email": "editor@teste.local", "senha": "123456"},
    )

    response = client.post(
        "/wiki/estatuto-basico-ampliado/editar",
        data={
            "titulo": "",
            "conteudo_markdown": "",
        },
    )
    assert response.status_code == 400


@pytest.mark.functional
def test_wiki_gestao_exige_autenticacao(client):
    response = client.get("/wiki/gestao")
    assert response.status_code == 302
    assert "/entrar?proximo=/wiki/gestao" in response.headers["Location"]


@pytest.mark.functional
def test_wiki_gestao_lista_paginas_para_editor(client):
    client.post(
        "/entrar",
        data={"email": "editor@teste.local", "senha": "123456"},
    )

    response = client.get("/wiki/gestao")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Gestao da Wiki" in html
    assert "Criar nova pagina" in html
    assert "Estatuto Basico Ampliado" in html


@pytest.mark.functional
def test_wiki_nova_exige_autenticacao(client):
    response = client.get("/wiki/nova")
    assert response.status_code == 302
    assert "/entrar?proximo=/wiki/nova" in response.headers["Location"]


@pytest.mark.functional
def test_wiki_nova_nao_usa_required_no_textarea_com_easymde(client):
    client.post(
        "/entrar",
        data={"email": "editor@teste.local", "senha": "123456"},
    )

    response = client.get("/wiki/nova")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<textarea id="conteudo_markdown" name="conteudo_markdown" rows="16">' in html
    assert 'name="conteudo_markdown" rows="16" required' not in html
    assert "alert('Conteudo e obrigatorio.')" in html


@pytest.mark.functional
def test_form_wiki_nova_aponta_para_endpoint_de_criacao(client):
    client.post(
        "/entrar",
        data={"email": "editor@teste.local", "senha": "123456"},
    )

    response = client.get("/wiki/nova")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<form method="post" action="/wiki/nova">' in html


@pytest.mark.functional
def test_wiki_nova_cria_pagina_com_editor(client):
    client.post(
        "/entrar",
        data={"email": "editor@teste.local", "senha": "123456"},
    )

    response = client.post(
        "/wiki/nova",
        data={
            "slug": "",
            "titulo": "Manifesto de Trabalho",
            "conteudo_markdown": "# Manifesto de Trabalho\n\nTexto inicial da pagina.",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Manifesto de Trabalho" in html
    assert "Texto inicial da pagina." in html


@pytest.mark.functional
def test_wiki_nova_retorna_400_para_slug_duplicado(client):
    client.post(
        "/entrar",
        data={"email": "editor@teste.local", "senha": "123456"},
    )

    response = client.post(
        "/wiki/nova",
        data={
            "slug": "estatuto-basico-ampliado",
            "titulo": "Duplicado",
            "conteudo_markdown": "# Duplicado\n\nTexto.",
        },
    )

    assert response.status_code == 400
    assert "Ja existe uma pagina com este slug." in response.get_data(as_text=True)


@pytest.mark.functional
def test_wiki_editar_nao_usa_required_no_textarea_com_easymde(client):
    client.post(
        "/entrar",
        data={"email": "editor@teste.local", "senha": "123456"},
    )

    response = client.get("/wiki/estatuto-basico-ampliado/editar")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<textarea id="conteudo_markdown" name="conteudo_markdown" rows="16">' in html
    assert 'name="conteudo_markdown" rows="16" required' not in html
    assert "alert('Conteudo e obrigatorio.')" in html


@pytest.mark.functional
def test_form_wiki_editar_aponta_para_endpoint_de_edicao(client):
    client.post(
        "/entrar",
        data={"email": "editor@teste.local", "senha": "123456"},
    )

    response = client.get("/wiki/estatuto-basico-ampliado/editar")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<form method="post" action="/wiki/estatuto-basico-ampliado/editar">' in html


@pytest.mark.functional
def test_login_logout_funciona_e_renderiza_estado_no_topo(client):
    home_anonimo = client.get("/").get_data(as_text=True)
    assert "Entrar" in home_anonimo

    login = client.post(
        "/entrar",
        data={"email": "editor@teste.local", "senha": "123456"},
        follow_redirects=True,
    )
    assert login.status_code == 200
    html_logado = login.get_data(as_text=True)
    assert "editor@teste.local (editor)" in html_logado

    logout = client.post("/sair", follow_redirects=True)
    assert logout.status_code == 200
    assert "Entrar" in logout.get_data(as_text=True)


@pytest.mark.functional
def test_login_invalido_retorna_401(client):
    response = client.post(
        "/entrar",
        data={"email": "editor@teste.local", "senha": "senha-errada"},
    )
    assert response.status_code == 401
    assert "Credenciais invalidas" in response.get_data(as_text=True)


@pytest.mark.functional
def test_form_login_aponta_para_endpoint_de_entrada(client):
    response = client.get("/entrar")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<form method="post" action="/entrar">' in html


@pytest.mark.functional
def test_login_ignora_destino_externo(client):
    response = client.post(
        "/entrar",
        data={"email": "editor@teste.local", "senha": "123456", "proximo": "https://externo.com"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/wiki/")


@pytest.mark.functional
def test_wiki_retorna_404_para_slug_inexistente(client):
    response = client.get("/wiki/pagina-inexistente")
    assert response.status_code == 404


@pytest.mark.functional
def test_admin_usuarios_exige_autenticacao(client):
    response = client.get("/admin/usuarios")
    assert response.status_code == 302
    assert "/entrar?proximo=/admin/usuarios" in response.headers["Location"]


@pytest.mark.functional
def test_admin_usuarios_bloqueia_editor(client):
    client.post(
        "/entrar",
        data={"email": "editor@teste.local", "senha": "123456"},
    )

    response = client.get("/admin/usuarios")
    assert response.status_code == 403


@pytest.mark.functional
def test_admin_usuarios_cria_atualiza_e_desativa_usuario(client):
    client.post(
        "/entrar",
        data={"email": "admin@teste.local", "senha": "abc123"},
    )

    criar = client.post(
        "/admin/usuarios",
        data={
            "email": "novo.usuario@teste.local",
            "senha": "senha123",
            "papel": "nao_editor",
        },
        follow_redirects=True,
    )
    assert criar.status_code == 200

    with client.application.app_context():
        usuario = Usuario.query.filter_by(email="novo.usuario@teste.local").first()
        assert usuario is not None
        usuario_id = usuario.id

    atualizar = client.post(
        f"/admin/usuarios/{usuario_id}/atualizar",
        data={"papel": "editor", "senha": ""},
        follow_redirects=True,
    )
    assert atualizar.status_code == 200

    with client.application.app_context():
        atualizado = Usuario.query.filter_by(id=usuario_id).first()
        assert atualizado is not None
        assert atualizado.papel == "editor"

    desativar = client.post(
        f"/admin/usuarios/{usuario_id}/desativar",
        follow_redirects=True,
    )
    assert desativar.status_code == 200

    with client.application.app_context():
        desativado = Usuario.query.filter_by(id=usuario_id).first()
        assert desativado is not None
        assert desativado.ativo is False


@pytest.mark.functional
def test_form_admin_criar_usuario_aponta_para_endpoint_de_criacao(client):
    client.post(
        "/entrar",
        data={"email": "admin@teste.local", "senha": "abc123"},
    )

    response = client.get("/admin/usuarios")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<form method="post" action="/admin/usuarios">' in html


@pytest.mark.functional
def test_admin_usuarios_reativa_usuario(client):
    client.post(
        "/entrar",
        data={"email": "admin@teste.local", "senha": "abc123"},
    )

    with client.application.app_context():
        usuario = Usuario.query.filter_by(email="editor@teste.local").first()
        assert usuario is not None
        usuario.ativo = False
        usuario_id = usuario.id
        from app.dados.base import db

        db.session.commit()

    response = client.post(
        f"/admin/usuarios/{usuario_id}/ativar",
        follow_redirects=True,
    )
    assert response.status_code == 200

    with client.application.app_context():
        reativado = Usuario.query.filter_by(id=usuario_id).first()
        assert reativado is not None
        assert reativado.ativo is True


@pytest.mark.functional
def test_admin_usuarios_criar_duplicado_retorna_400(client):
    client.post(
        "/entrar",
        data={"email": "admin@teste.local", "senha": "abc123"},
    )

    response = client.post(
        "/admin/usuarios",
        data={
            "email": "editor@teste.local",
            "senha": "123456",
            "papel": "editor",
        },
    )

    assert response.status_code == 400
    assert "Ja existe usuario com esse email" in response.get_data(as_text=True)


@pytest.mark.functional
def test_admin_usuarios_atualizar_inexistente_retorna_404(client):
    client.post(
        "/entrar",
        data={"email": "admin@teste.local", "senha": "abc123"},
    )

    response = client.post("/admin/usuarios/9999/atualizar", data={"papel": "editor", "senha": ""})
    assert response.status_code == 404


@pytest.mark.functional
def test_admin_usuarios_desativar_inexistente_retorna_404(client):
    client.post(
        "/entrar",
        data={"email": "admin@teste.local", "senha": "abc123"},
    )

    response = client.post("/admin/usuarios/9999/desativar")
    assert response.status_code == 404


@pytest.mark.functional
def test_admin_usuarios_ativar_inexistente_retorna_404(client):
    client.post(
        "/entrar",
        data={"email": "admin@teste.local", "senha": "abc123"},
    )

    response = client.post("/admin/usuarios/9999/ativar")
    assert response.status_code == 404


@pytest.mark.functional
def test_admin_usuarios_bloqueia_autodemocao_de_papel(client):
    client.post(
        "/entrar",
        data={"email": "admin@teste.local", "senha": "abc123"},
    )

    with client.application.app_context():
        admin = Usuario.query.filter_by(email="admin@teste.local").first()
        assert admin is not None
        admin_id = admin.id

    response = client.post(
        f"/admin/usuarios/{admin_id}/atualizar",
        data={"papel": "editor", "senha": ""},
    )

    assert response.status_code == 400
    assert "Nao e permitido remover seu proprio papel de admin." in response.get_data(as_text=True)

    with client.application.app_context():
        admin = Usuario.query.filter_by(id=admin_id).first()
        assert admin is not None
        assert admin.papel == "admin"


@pytest.mark.functional
def test_admin_usuarios_bloqueia_autodesativacao(client):
    client.post(
        "/entrar",
        data={"email": "admin@teste.local", "senha": "abc123"},
    )

    with client.application.app_context():
        admin = Usuario.query.filter_by(email="admin@teste.local").first()
        assert admin is not None
        admin_id = admin.id

    response = client.post(f"/admin/usuarios/{admin_id}/desativar")
    assert response.status_code == 400
    assert "Nao e permitido desativar seu proprio usuario admin." in response.get_data(as_text=True)

    with client.application.app_context():
        admin = Usuario.query.filter_by(id=admin_id).first()
        assert admin is not None
        assert admin.ativo is True
