import pytest

from app.dados import db
from app.dados.modelos import ConfiguracaoPublica, WikiPagina
from app.domain import paginas_gerais as servico


@pytest.mark.unit
def test_carregar_configuracoes_paginas_gerais_retorna_defaults_quando_vazio(app_instance):
    with app_instance.app_context():
        db.session.query(ConfiguracaoPublica).delete()
        db.session.commit()

        cfg = servico.carregar_configuracoes_paginas_gerais()

        assert cfg[servico.CHAVE_WIKI_ESTATUTO] == ""
        assert cfg[servico.CHAVE_WIKI_POLITICA_PRIVACIDADE] == ""
        assert cfg[servico.CHAVE_WIKI_TERMOS_USO] == ""


@pytest.mark.unit
def test_atualizar_configuracoes_paginas_gerais_cria_registros_novos(app_instance):
    with app_instance.app_context():
        db.session.query(ConfiguracaoPublica).delete()

        db.session.add_all(
            [
                WikiPagina(slug="estatuto-unit", titulo="Estatuto Unit", conteudo_markdown="# E"),
                WikiPagina(slug="politica-unit", titulo="Politica Unit", conteudo_markdown="# P"),
                WikiPagina(slug="termos-unit", titulo="Termos Unit", conteudo_markdown="# T"),
            ]
        )
        db.session.commit()

        servico.atualizar_configuracoes_paginas_gerais(
            estatuto_slug=" estatuto-unit ",
            politica_slug="politica-unit",
            termos_slug="termos-unit",
        )

        registros = {item.chave: item.valor for item in ConfiguracaoPublica.query.all()}
        assert registros[servico.CHAVE_WIKI_ESTATUTO] == "estatuto-unit"
        assert registros[servico.CHAVE_WIKI_POLITICA_PRIVACIDADE] == "politica-unit"
        assert registros[servico.CHAVE_WIKI_TERMOS_USO] == "termos-unit"


@pytest.mark.unit
def test_atualizar_configuracoes_paginas_gerais_rejeita_slug_inexistente(app_instance):
    with app_instance.app_context():
        with pytest.raises(ValueError, match="wiki_slug_estatuto"):
            servico.atualizar_configuracoes_paginas_gerais(
                estatuto_slug="nao-existe",
                politica_slug="",
                termos_slug="",
            )


@pytest.mark.unit
def test_carregar_links_paginas_gerais_resolve_e_ignora_slug_sem_pagina(app_instance):
    with app_instance.app_context():
        db.session.query(ConfiguracaoPublica).delete()

        db.session.add(WikiPagina(slug="politica-unit", titulo="", conteudo_markdown="# Politica Real"))
        db.session.add_all(
            [
                ConfiguracaoPublica(chave=servico.CHAVE_WIKI_ESTATUTO, valor="slug-inexistente"),
                ConfiguracaoPublica(chave=servico.CHAVE_WIKI_POLITICA_PRIVACIDADE, valor="politica-unit"),
                ConfiguracaoPublica(chave=servico.CHAVE_WIKI_TERMOS_USO, valor=""),
            ]
        )
        db.session.commit()

        links = servico.carregar_links_paginas_gerais()

        assert links["estatuto"] is None
        assert links["termos_uso"] is None
        assert links["politica_privacidade"] == {
            "slug": "politica-unit",
            "titulo": "Política de Privacidade",
            "url": "/wiki/politica-unit",
        }


@pytest.mark.unit
def test_atualizar_configuracoes_paginas_gerais_atualiza_registros_existentes(app_instance):
    with app_instance.app_context():
        db.session.query(ConfiguracaoPublica).delete()

        db.session.add_all(
            [
                WikiPagina(slug="e-1", titulo="E1", conteudo_markdown="# E1"),
                WikiPagina(slug="e-2", titulo="E2", conteudo_markdown="# E2"),
                WikiPagina(slug="p-1", titulo="P1", conteudo_markdown="# P1"),
                WikiPagina(slug="t-1", titulo="T1", conteudo_markdown="# T1"),
            ]
        )
        db.session.add_all(
            [
                ConfiguracaoPublica(chave=servico.CHAVE_WIKI_ESTATUTO, valor="e-1"),
                ConfiguracaoPublica(chave=servico.CHAVE_WIKI_POLITICA_PRIVACIDADE, valor="p-1"),
                ConfiguracaoPublica(chave=servico.CHAVE_WIKI_TERMOS_USO, valor="t-1"),
            ]
        )
        db.session.commit()

        servico.atualizar_configuracoes_paginas_gerais(
            estatuto_slug="e-2",
            politica_slug="p-1",
            termos_slug="",
        )

        registros = {item.chave: item.valor for item in ConfiguracaoPublica.query.all()}
        assert registros[servico.CHAVE_WIKI_ESTATUTO] == "e-2"
        assert registros[servico.CHAVE_WIKI_POLITICA_PRIVACIDADE] == "p-1"
        assert registros[servico.CHAVE_WIKI_TERMOS_USO] == ""
