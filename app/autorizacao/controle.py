from collections.abc import Callable
from functools import wraps

from flask import abort, g, redirect, request, url_for

from .papeis import tem_permissao


def exigir_permissao(
    recurso: str,
    acao: str,
    get_papel: Callable[[], str | None] | None = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not get_papel and not getattr(g, "usuario_email", None):
                return redirect(url_for("autenticacao.entrar", proximo=request.path))

            papel = get_papel() if get_papel else getattr(g, "papel_atual", None)

            if not tem_permissao(papel, recurso, acao):
                abort(403)

            return func(*args, **kwargs)

        return wrapper

    return decorator
