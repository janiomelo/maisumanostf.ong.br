import pytest

from app.dados.modelos import Usuario
import app.cli.db as cli_db


@pytest.mark.unit
def test_cli_criar_usuario_com_sucesso(app_instance):
    runner = app_instance.test_cli_runner()

    resultado = runner.invoke(
        args=[
            "criar-usuario",
            "--email",
            "cli-editor@teste.local",
            "--senha",
            "123456",
            "--papel",
            "editor",
        ]
    )

    assert resultado.exit_code == 0
    assert "Usuario criado: cli-editor@teste.local (editor)" in resultado.output

    with app_instance.app_context():
        usuario = Usuario.query.filter_by(email="cli-editor@teste.local").first()
        assert usuario is not None
        assert usuario.papel == "editor"


@pytest.mark.unit
def test_cli_criar_usuario_retorna_erro_para_email_duplicado(app_instance):
    runner = app_instance.test_cli_runner()

    resultado = runner.invoke(
        args=[
            "criar-usuario",
            "--email",
            "editor@teste.local",
            "--senha",
            "123456",
            "--papel",
            "editor",
        ]
    )

    assert resultado.exit_code != 0
    assert "Error: Já existe usuário com esse e-mail" in resultado.output


@pytest.mark.unit
def test_cli_db_update_seguro_executa_upgrade(app_instance, monkeypatch):
    runner = app_instance.test_cli_runner()
    chamadas = {"upgrade": 0}

    def _upgrade_falso(app):
        assert app == app_instance
        chamadas["upgrade"] += 1

    monkeypatch.setattr(cli_db, "aplicar_upgrade_seguro", _upgrade_falso)

    resultado = runner.invoke(args=["db-update-seguro"])

    assert resultado.exit_code == 0
    assert chamadas["upgrade"] == 1
    assert "Migracoes aplicadas com sucesso." in resultado.output
