import click
from flask import Flask

from app.autenticacao import criar_usuario


def registrar_comandos_usuarios(app: Flask) -> None:
    @app.cli.command("criar-usuario")
    @click.option("--email", required=True, help="Email do usuario")
    @click.option("--senha", required=True, help="Senha inicial")
    @click.option("--papel", default="nao_editor", help="Papel: nao_editor, editor ou admin")
    def criar_usuario_cmd(email: str, senha: str, papel: str) -> None:
        try:
            usuario = criar_usuario(email=email, senha=senha, papel=papel)
        except ValueError as exc:
            raise click.ClickException(str(exc))

        click.echo(f"Usuario criado: {usuario.email} ({usuario.papel})")
