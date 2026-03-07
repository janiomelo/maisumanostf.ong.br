import pytest
from flask import Flask

from app.autorizacao.controle import exigir_permissao
from app.autorizacao.papeis import normalizar_papel, tem_permissao


@pytest.mark.unit
def test_normalizar_papel_aplica_default_para_none_e_invalido():
    assert normalizar_papel(None) == "nao_editor"
    assert normalizar_papel("desconhecido") == "nao_editor"


@pytest.mark.unit
def test_normalizar_papel_suporta_caixa_e_espacos():
    assert normalizar_papel(" Editor ") == "editor"


@pytest.mark.unit
def test_matriz_de_permissoes_inicial():
    assert tem_permissao("nao_editor", "wiki", "ler") is True
    assert tem_permissao("nao_editor", "wiki", "editar") is False

    assert tem_permissao("editor", "wiki", "editar") is True
    assert tem_permissao("editor", "wiki", "publicar") is True

    assert tem_permissao("admin", "wiki", "arquivar") is True


@pytest.mark.unit
def test_decorator_exigir_permissao_libera_quando_autorizado():
    app = Flask(__name__)

    @app.get("/wiki/editar")
    @exigir_permissao("wiki", "editar", get_papel=lambda: "editor")
    def wiki_editar():
        return "ok"

    client = app.test_client()
    response = client.get("/wiki/editar")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "ok"


@pytest.mark.unit
def test_decorator_exigir_permissao_bloqueia_quando_nao_autorizado():
    app = Flask(__name__)

    @app.get("/wiki/publicar")
    @exigir_permissao("wiki", "publicar", get_papel=lambda: "nao_editor")
    def wiki_publicar():
        return "ok"

    client = app.test_client()
    response = client.get("/wiki/publicar")

    assert response.status_code == 403
