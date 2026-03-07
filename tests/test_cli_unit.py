import pytest

from app.dados.modelos import Usuario


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
    assert "Error: Ja existe usuario com esse email" in resultado.output
