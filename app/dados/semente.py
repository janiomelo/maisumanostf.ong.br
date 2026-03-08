from .base import db
from .modelos import ConfiguracaoPublica, WikiPagina

CHAVE_WIKI_ESTATUTO = "wiki_slug_estatuto"
CHAVE_WIKI_POLITICA_PRIVACIDADE = "wiki_slug_politica_privacidade"
CHAVE_WIKI_TERMOS_USO = "wiki_slug_termos_uso"

CONTEUDO_WIKI_INICIAL = """# Estatuto Basico Ampliado

Documento em construcao para consolidar principios, governanca e diretrizes publicas da campanha.

## Escopo inicial

Finalidade civica e institucional da campanha.
Compromissos de transparencia e revisao publica de dados.
Estrutura de papeis e responsabilidades editoriais.

## Nota

Esta versao e um ponto de partida estrutural. O conteudo detalhado sera ampliado na proxima etapa.
"""

CONTEUDO_ESTATUTO_BASE = """# Estatuto Base

Versao de referencia do estatuto da campanha, com diretrizes de governanca e compromisso publico.

## Principios

Representatividade minima feminina no STF.
Transparencia sobre os dados e limites da campanha.
Revisao publica dos textos institucionais.
"""

CONTEUDO_POLITICA_PRIVACIDADE = """# Politica de Privacidade

Esta pagina descreve de forma objetiva quais dados sao coletados e com qual finalidade.

## Dados tratados

Dados de autenticacao.
Registro de apoio e data de adesao.

## Finalidade

Permitir participacao autenticada, comunicacao institucional e transparencia da campanha.
"""

CONTEUDO_TERMOS_USO = """# Termos de Uso

Esta pagina define regras de uso do site e limites da plataforma.

## Uso permitido

Consulta publica de conteudo e participacao conforme as regras da campanha.

## Responsabilidades

Usuarios devem usar informacoes verdadeiras e respeitar as diretrizes de convivio civico.
"""


def semear_wiki_inicial() -> None:
    paginas_base = [
        ("estatuto-basico-ampliado", "Estatuto Basico Ampliado", CONTEUDO_WIKI_INICIAL),
        ("estatuto-base", "Estatuto Base", CONTEUDO_ESTATUTO_BASE),
        ("politica-de-privacidade", "Politica de Privacidade", CONTEUDO_POLITICA_PRIVACIDADE),
        ("termos-de-uso", "Termos de Uso", CONTEUDO_TERMOS_USO),
    ]

    for slug, titulo, conteudo in paginas_base:
        existe = WikiPagina.query.filter_by(slug=slug).first()
        if existe:
            continue

        db.session.add(
            WikiPagina(
                slug=slug,
                titulo=titulo,
                conteudo_markdown=conteudo,
            )
        )

    configuracoes_padrao = {
        CHAVE_WIKI_ESTATUTO: "estatuto-base",
        CHAVE_WIKI_POLITICA_PRIVACIDADE: "politica-de-privacidade",
        CHAVE_WIKI_TERMOS_USO: "termos-de-uso",
    }

    for chave, valor in configuracoes_padrao.items():
        existe = ConfiguracaoPublica.query.filter_by(chave=chave).first()
        if existe:
            continue

        db.session.add(ConfiguracaoPublica(chave=chave, valor=valor))

    db.session.commit()
