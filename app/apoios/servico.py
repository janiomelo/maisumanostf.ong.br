from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
import math

from sqlalchemy import or_, func

from app.dados.modelos import ApoioManifesto
from app.dados.base import db


@dataclass(frozen=True)
class ResultadoListagemApoios:
    apoios: list[ApoioManifesto]
    total_geral: int
    total_filtrado: int
    pagina: int
    por_pagina: int
    total_paginas: int


def listar_apoios_admin(
    *,
    termo: str,
    data_inicial: str,
    data_final: str,
    pagina: int,
    por_pagina: int,
) -> ResultadoListagemApoios:
    termo_normalizado = termo.strip().lower()
    pagina_normalizada = max(1, int(pagina))
    por_pagina_normalizado = max(1, min(int(por_pagina), 100))

    query = ApoioManifesto.query

    if termo_normalizado:
        like = f"%{termo_normalizado}%"
        query = query.filter(
            or_(
                func.lower(ApoioManifesto.email).like(like),
                func.lower(ApoioManifesto.nome).like(like),
            )
        )

    inicio = _parse_data_bruta(data_inicial)
    if inicio:
        query = query.filter(ApoioManifesto.criado_em >= datetime.combine(inicio, time.min))

    fim = _parse_data_bruta(data_final)
    if fim:
        query = query.filter(ApoioManifesto.criado_em < datetime.combine(fim + timedelta(days=1), time.min))

    total_geral = ApoioManifesto.query.count()
    total_filtrado = query.count()

    total_paginas = max(1, math.ceil(total_filtrado / por_pagina_normalizado))
    pagina_ajustada = min(pagina_normalizada, total_paginas)

    apoios = (
        query.order_by(ApoioManifesto.criado_em.desc(), ApoioManifesto.id.desc())
        .offset((pagina_ajustada - 1) * por_pagina_normalizado)
        .limit(por_pagina_normalizado)
        .all()
    )

    return ResultadoListagemApoios(
        apoios=apoios,
        total_geral=total_geral,
        total_filtrado=total_filtrado,
        pagina=pagina_ajustada,
        por_pagina=por_pagina_normalizado,
        total_paginas=total_paginas,
    )


def remover_apoio_admin(apoio_id: int) -> bool:
    apoio = ApoioManifesto.query.filter_by(id=apoio_id).first()
    if not apoio:
        return False

    db.session.delete(apoio)
    db.session.commit()
    return True


def _parse_data_bruta(valor: str):
    bruto = valor.strip()
    if not bruto:
        return None

    try:
        return datetime.strptime(bruto, "%Y-%m-%d").date()
    except ValueError:
        return None
