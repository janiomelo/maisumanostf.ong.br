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
        assert "<h2>Secao</h2>" in pagina["conteudo_html"]
        assert "conteudo_markdown" in pagina
        assert "criado_em" in pagina
        assert "atualizado_em" in pagina


@pytest.mark.unit
def test_carregar_pagina_wiki_renderiza_markdown_com_lista_e_link(app_instance):
    with app_instance.app_context():
        db.session.add(
            WikiPagina(
                slug="markdown-avancado",
                titulo="Markdown Avancado",
                conteudo_markdown="# Markdown Avancado\n\nTexto com **destaque** e [link](https://example.com).\n\n- Item 1\n- Item 2",
            )
        )
        db.session.commit()

        pagina = wiki.carregar_pagina_wiki("markdown-avancado")

        assert pagina is not None
        html = pagina["conteudo_html"]
        assert "<strong>destaque</strong>" in html
        assert '<a href="https://example.com" rel="noopener">link</a>' in html
        assert "<ul><li>Item 1</li><li>Item 2</li></ul>" in html


@pytest.mark.unit
def test_carregar_pagina_wiki_escapa_html_perigoso(app_instance):
    with app_instance.app_context():
        db.session.add(
            WikiPagina(
                slug="html-perigoso",
                titulo="HTML Perigoso",
                conteudo_markdown="# HTML Perigoso\n\n<script>alert('x')</script>",
            )
        )
        db.session.commit()

        pagina = wiki.carregar_pagina_wiki("html-perigoso")

        assert pagina is not None
        html = pagina["conteudo_html"]
        assert "<script>" not in html
        assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in html


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


@pytest.mark.unit
def test_listar_paginas_wiki_usa_resumo_padrao_quando_sem_paragrafo(app_instance):
    with app_instance.app_context():
        db.session.add(
            WikiPagina(
                slug="somente-secao",
                titulo="",
                conteudo_markdown="# Titulo Sem Resumo\n\n## Secao",
            )
        )
        db.session.commit()

        paginas = wiki.listar_paginas_wiki()
        pagina = next(item for item in paginas if item["slug"] == "somente-secao")

        assert pagina["titulo"] == "Titulo Sem Resumo"
        assert pagina["resumo"] == "Sem resumo."


@pytest.mark.unit
def test_carregar_pagina_wiki_renderiza_blocos_markdown_restantes(app_instance):
    with app_instance.app_context():
        db.session.add(
            WikiPagina(
                slug="markdown-completo",
                titulo="Markdown Completo",
                conteudo_markdown=(
                    "# Markdown Completo\n\n"
                    "### Subtitulo\n\n"
                    "1. Primeiro\n2. Segundo\n\n"
                    "```\n"
                    "print('<x>')\n"
                    "```\n\n"
                    "Texto antes\ncontinua na mesma ideia\n\n"
                    "## Encerramento\n"
                ),
            )
        )
        db.session.commit()

        pagina = wiki.carregar_pagina_wiki("markdown-completo")

        assert pagina is not None
        html = pagina["conteudo_html"]
        assert "<h3>Subtitulo</h3>" in html
        assert "<ol><li>Primeiro</li><li>Segundo</li></ol>" in html
        assert "<pre><code>print(&#x27;&lt;x&gt;&#x27;)</code></pre>" in html
        assert "<p>Texto antes continua na mesma ideia</p>" in html
        assert "<h2>Encerramento</h2>" in html


@pytest.mark.unit
def test_carregar_pagina_wiki_link_invalido_fica_escapado(app_instance):
    with app_instance.app_context():
        db.session.add(
            WikiPagina(
                slug="link-invalido",
                titulo="Link Invalido",
                conteudo_markdown="# Link Invalido\n\n[ataque](javascript:alert(1))",
            )
        )
        db.session.commit()

        pagina = wiki.carregar_pagina_wiki("link-invalido")

        assert pagina is not None
        html = pagina["conteudo_html"]
        assert '<a href="javascript:alert(1)"' not in html
        assert "[ataque](javascript:alert(1))" in html


@pytest.mark.unit
def test_atualizar_pagina_wiki_retorna_none_para_slug_invalido_ou_inexistente(app_instance):
    with app_instance.app_context():
        assert wiki.atualizar_pagina_wiki("../invalido", "Titulo", "# Titulo") is None
        assert wiki.atualizar_pagina_wiki("nao-existe", "Titulo", "# Titulo") is None


@pytest.mark.unit
def test_criar_pagina_wiki_falha_se_recarga_pos_commit_retorna_none(app_instance, monkeypatch):
    with app_instance.app_context():
        original = wiki.carregar_pagina_wiki

        def _retorna_none_apenas_na_nova(slug: str):
            if slug == "falha-recarga":
                return None
            return original(slug)

        monkeypatch.setattr(wiki, "carregar_pagina_wiki", _retorna_none_apenas_na_nova)

        with pytest.raises(ValueError, match="Falha ao carregar página após criação"):
            wiki.criar_pagina_wiki(
                slug="falha-recarga",
                titulo="Falha Recarga",
                conteudo_markdown="# Falha Recarga\n\nConteudo",
            )


@pytest.mark.unit
def test_carregar_pagina_wiki_sem_h1_usa_titulo_padrao_parse(app_instance):
    with app_instance.app_context():
        db.session.add(
            WikiPagina(
                slug="sem-h1",
                titulo="",
                conteudo_markdown="Texto inicial sem h1.",
            )
        )
        db.session.commit()

        pagina = wiki.carregar_pagina_wiki("sem-h1")

        assert pagina is not None
        assert pagina["titulo"] == "Página Wiki"


@pytest.mark.unit
def test_carregar_pagina_wiki_renderiza_link_relativo_e_quebra_paragrafo(app_instance):
    with app_instance.app_context():
        db.session.add(
            WikiPagina(
                slug="quebra-paragrafo",
                titulo="Quebra",
                conteudo_markdown=(
                    "# Quebra\n\n"
                    "linha 1 [interno](/wiki/abc)\n"
                    "## Nova secao\n"
                    "linha 2\n"
                    "- item"
                ),
            )
        )
        db.session.commit()

        pagina = wiki.carregar_pagina_wiki("quebra-paragrafo")

        assert pagina is not None
        html = pagina["conteudo_html"]
        assert '<a href="/wiki/abc" rel="noopener">interno</a>' in html
        assert "<h2>Nova secao</h2>" in html
        assert "<ul><li>item</li></ul>" in html


@pytest.mark.unit
def test_atualizar_pagina_wiki_atualiza_com_sucesso(app_instance):
    with app_instance.app_context():
        db.session.add(
            WikiPagina(
                slug="atualizar-ok",
                titulo="Titulo Antigo",
                conteudo_markdown="# Antigo\n\nTexto antigo",
            )
        )
        db.session.commit()

        atualizada = wiki.atualizar_pagina_wiki(
            "atualizar-ok",
            "  Titulo Novo  ",
            "  # Novo\n\nTexto novo  ",
        )

        assert atualizada is not None
        assert atualizada["titulo"] == "Titulo Novo"
        assert "Texto novo" in atualizada["conteudo_markdown"]
