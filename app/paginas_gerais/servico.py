from __future__ import annotations

from app.dados.base import db
from app.dados.modelos import ConfiguracaoPublica, WikiPagina

CHAVE_WIKI_ESTATUTO = "wiki_slug_estatuto"
CHAVE_WIKI_POLITICA_PRIVACIDADE = "wiki_slug_politica_privacidade"
CHAVE_WIKI_TERMOS_USO = "wiki_slug_termos_uso"


def carregar_configuracoes_paginas_gerais() -> dict[str, str]:
    registros = {
        item.chave: item.valor
        for item in ConfiguracaoPublica.query.filter(
            ConfiguracaoPublica.chave.in_(
                [CHAVE_WIKI_ESTATUTO, CHAVE_WIKI_POLITICA_PRIVACIDADE, CHAVE_WIKI_TERMOS_USO]
            )
        ).all()
    }

    return {
        CHAVE_WIKI_ESTATUTO: str(registros.get(CHAVE_WIKI_ESTATUTO, "") or ""),
        CHAVE_WIKI_POLITICA_PRIVACIDADE: str(registros.get(CHAVE_WIKI_POLITICA_PRIVACIDADE, "") or ""),
        CHAVE_WIKI_TERMOS_USO: str(registros.get(CHAVE_WIKI_TERMOS_USO, "") or ""),
    }


def atualizar_configuracoes_paginas_gerais(*, estatuto_slug: str, politica_slug: str, termos_slug: str) -> None:
    payload = {
        CHAVE_WIKI_ESTATUTO: estatuto_slug.strip(),
        CHAVE_WIKI_POLITICA_PRIVACIDADE: politica_slug.strip(),
        CHAVE_WIKI_TERMOS_USO: termos_slug.strip(),
    }

    for chave, slug in payload.items():
        if slug and not WikiPagina.query.filter_by(slug=slug).first():
            raise ValueError(f"Slug informado para {chave} não existe na wiki.")

    for chave, slug in payload.items():
        registro = ConfiguracaoPublica.query.filter_by(chave=chave).first()
        if registro:
            registro.valor = slug
        else:
            db.session.add(ConfiguracaoPublica(chave=chave, valor=slug))

    db.session.commit()


def carregar_links_paginas_gerais() -> dict[str, dict[str, str] | None]:
    cfg = carregar_configuracoes_paginas_gerais()

    def _resolver(slug: str, titulo_padrao: str) -> dict[str, str] | None:
        slug_limpo = slug.strip()
        if not slug_limpo:
            return None

        pagina = WikiPagina.query.filter_by(slug=slug_limpo).first()
        if not pagina:
            return None

        return {
            "slug": slug_limpo,
            "titulo": pagina.titulo or titulo_padrao,
            "url": f"/wiki/{slug_limpo}",
        }

    return {
        "estatuto": _resolver(cfg[CHAVE_WIKI_ESTATUTO], "Transparência e Governança"),
        "politica_privacidade": _resolver(cfg[CHAVE_WIKI_POLITICA_PRIVACIDADE], "Política de Privacidade"),
        "termos_uso": _resolver(cfg[CHAVE_WIKI_TERMOS_USO], "Termos de Uso"),
    }
