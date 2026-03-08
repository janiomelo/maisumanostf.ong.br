from authlib.integrations.flask_client import OAuth


oauth = OAuth()


class GoogleOAuthError(RuntimeError):
    pass


def google_oauth_esta_configurado(config: dict) -> bool:
    return bool(config.get("GOOGLE_OAUTH_ENABLED")) and bool(config.get("GOOGLE_CLIENT_ID")) and bool(
        config.get("GOOGLE_CLIENT_SECRET")
    )


def inicializar_google_oauth(app) -> None:
    oauth.init_app(app)

    if not google_oauth_esta_configurado(app.config):
        return

    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url=app.config["GOOGLE_DISCOVERY_URL"],
        client_kwargs={"scope": "openid email profile"},
    )


def obter_cliente_google():
    cliente = oauth.create_client("google")
    if cliente is None:
        raise GoogleOAuthError("Cliente OAuth do Google nao inicializado.")

    return cliente


def trocar_codigo_por_usuario_google() -> dict:
    cliente = obter_cliente_google()

    try:
        token = cliente.authorize_access_token()
    except Exception as exc:  # pragma: no cover
        raise GoogleOAuthError("Falha ao obter token de acesso do Google.") from exc

    userinfo = token.get("userinfo") if isinstance(token, dict) else None
    if not isinstance(userinfo, dict):
        try:
            userinfo = cliente.userinfo(token=token)
            if hasattr(userinfo, "json"):
                userinfo = userinfo.json()
        except Exception as exc:  # pragma: no cover
            raise GoogleOAuthError("Falha ao consultar perfil do usuario no Google.") from exc

    if not isinstance(userinfo, dict):
        raise GoogleOAuthError("Resposta invalida do Google para perfil do usuario.")

    return {
        "sub": str(userinfo.get("sub", "")).strip(),
        "email": str(userinfo.get("email", "")).strip().lower(),
        "email_verified": bool(userinfo.get("email_verified", False)),
        "name": str(userinfo.get("name", "")).strip(),
    }
