import click
from flask import Flask

from app.dados.migracoes import aplicar_upgrade_seguro


def registrar_comandos_db(app: Flask) -> None:
    @app.cli.command("db-update-seguro")
    def db_update_seguro_cmd() -> None:
        aplicar_upgrade_seguro(app)
        click.echo("Migracoes aplicadas com sucesso.")
