PAPEIS_VALIDOS = ("nao_editor", "editor", "admin")

# Matriz inicial de permissao por recurso/acao para evolucao gradual de RBAC.
_PERMISSOES_POR_PAPEL: dict[str, set[tuple[str, str]]] = {
    "nao_editor": {
        ("wiki", "ler"),
    },
    "editor": {
        ("wiki", "ler"),
        ("wiki", "criar"),
        ("wiki", "editar"),
        ("wiki", "publicar"),
    },
    "admin": {
        ("*", "*"),
    },
}


def normalizar_papel(papel: str | None) -> str:
    if not papel:
        return "nao_editor"

    papel_normalizado = papel.strip().lower()
    if papel_normalizado in PAPEIS_VALIDOS:
        return papel_normalizado

    return "nao_editor"


def tem_permissao(papel: str | None, recurso: str, acao: str) -> bool:
    papel_normalizado = normalizar_papel(papel)
    permissoes = _PERMISSOES_POR_PAPEL[papel_normalizado]

    if ("*", "*") in permissoes:
        return True

    return (recurso, acao) in permissoes
