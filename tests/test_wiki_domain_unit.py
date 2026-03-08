import pytest

from app.domain import wiki
from app.dados import WikiPagina, db


@pytest.mark.unit
def test_listar_paginas_wiki_ler_do_banco(app_instance):
    with app_instance.app_context():
        db.session.add(
            WikiPagina(
                slug="pagina-de-teste",
                titulo="Pagina de Teste",
                conteudo_markdown="# Pagina de Teste\n\nResumo de teste.",
            )
        )
        db.session.commit()

        paginas = wiki.listar_paginas_wiki()

        slugs = {item["slug"] for item in paginas}
        assert "estatuto-basico-ampliado" in slugs
        assert "pagina-de-teste" in slugs


@pytest.mark.unit
def test_carregar_pagina_wiki_retorna_blocos_do_banco(app_instance):
    with app_instance.app_context():
        db.session.add(
            WikiPagina(
                slug="estatuto-teste",
                titulo="Estatuto Teste",
                conteudo_markdown="# Estatuto Teste\n\nIntroducao.\n\n## Secao\n\nTexto da secao.",
            )
        )
        db.session.commit()

        pagina = wiki.carregar_pagina_wiki("estatuto-teste")

        assert pagina is not None
        assert pagina["slug"] == "estatuto-teste"
        assert pagina["titulo"] == "Estatuto Teste"
        assert any(bloco["tipo"] == "h2" and bloco["texto"] == "Secao" for bloco in pagina["blocos"])
        assert "conteudo_markdown" in pagina


@pytest.mark.unit
def test_carregar_pagina_wiki_rejeita_slug_invalido(app_instance):
    with app_instance.app_context():
        assert wiki.carregar_pagina_wiki("../hack") is None


@pytest.mark.unit
def test_carregar_pagina_wiki_inexistente_retorna_none(app_instance):
    with app_instance.app_context():
        assert wiki.carregar_pagina_wiki("slug-inexistente") is None


@pytest.mark.unit
def test_criar_pagina_wiki_com_slug_automatico(app_instance):
    with app_instance.app_context():
        pagina = wiki.criar_pagina_wiki(
            slug="",
            titulo="Nova Pagina de Agenda",
            conteudo_markdown="# Nova Pagina de Agenda\n\nConteudo inicial.",
        )

        assert pagina["slug"] == "nova-pagina-de-agenda"
        assert pagina["titulo"] == "Nova Pagina de Agenda"


@pytest.mark.unit
def test_criar_pagina_wiki_rejeita_slug_duplicado(app_instance):
    with app_instance.app_context():
        with pytest.raises(ValueError, match="Já existe uma página com este slug"):
            wiki.criar_pagina_wiki(
                slug="estatuto-basico-ampliado",
                titulo="Outro Estatuto",
                conteudo_markdown="# Outro Estatuto\n\nDuplicado.",
            )


@pytest.mark.unit
def test_criar_pagina_wiki_rejeita_payload_invalido(app_instance):
    with app_instance.app_context():
        with pytest.raises(ValueError, match="Título e conteúdo são obrigatórios"):
            wiki.criar_pagina_wiki(slug="nova", titulo="", conteudo_markdown="")

        with pytest.raises(ValueError, match="Slug inválido"):
            wiki.criar_pagina_wiki(
                slug="../invalido",
                titulo="Titulo valido",
                conteudo_markdown="# Titulo valido\n\nTexto.",
            )
