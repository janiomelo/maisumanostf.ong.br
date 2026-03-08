import pytest

from app.dados import migracoes


@pytest.mark.unit
def test_definir_stamp_legado_sem_alembic_so_wiki():
    tabelas = {"wiki_paginas"}
    assert migracoes._definir_stamp_legado(tabelas) == "96097c95c490"


@pytest.mark.unit
def test_definir_stamp_legado_com_wiki_e_usuarios():
    tabelas = {"wiki_paginas", "usuarios"}
    assert migracoes._definir_stamp_legado(tabelas) == "2b4a1e6e5f9b"


@pytest.mark.unit
def test_definir_stamp_legado_sem_necessidade_de_stamp():
    tabelas = {"wiki_paginas", "usuarios"}
    assert migracoes._definir_stamp_legado(tabelas) == "2b4a1e6e5f9b"


@pytest.mark.unit
def test_definir_stamp_legado_sem_tabela_wiki():
    tabelas = {"alembic_version", "qualquer"}
    assert migracoes._definir_stamp_legado(tabelas) is None


@pytest.mark.unit
def test_aplicar_upgrade_seguro_executa_stamp_quando_necessario(app_instance, monkeypatch):
    eventos: list[tuple[str, str | None]] = []

    class InspectorFalso:
        @staticmethod
        def get_table_names():
            return ["wiki_paginas"]

    monkeypatch.setattr(migracoes, "inspect", lambda engine: InspectorFalso())
    monkeypatch.setattr(migracoes, "_historico_migracao_presente", lambda tabelas: False)
    monkeypatch.setattr(migracoes, "stamp", lambda revision: eventos.append(("stamp", revision)))
    monkeypatch.setattr(migracoes, "upgrade", lambda: eventos.append(("upgrade", None)))

    migracoes.aplicar_upgrade_seguro(app_instance)

    assert eventos == [("stamp", "96097c95c490"), ("upgrade", None)]


@pytest.mark.unit
def test_aplicar_upgrade_seguro_pula_stamp_quando_ja_tem_alembic(app_instance, monkeypatch):
    eventos: list[tuple[str, str | None]] = []

    class InspectorFalso:
        @staticmethod
        def get_table_names():
            return ["alembic_version", "wiki_paginas", "usuarios"]

    monkeypatch.setattr(migracoes, "inspect", lambda engine: InspectorFalso())
    monkeypatch.setattr(migracoes, "_historico_migracao_presente", lambda tabelas: True)
    monkeypatch.setattr(migracoes, "stamp", lambda revision: eventos.append(("stamp", revision)))
    monkeypatch.setattr(migracoes, "upgrade", lambda: eventos.append(("upgrade", None)))

    migracoes.aplicar_upgrade_seguro(app_instance)

    assert eventos == [("upgrade", None)]


@pytest.mark.unit
def test_historico_migracao_presente_quando_alembic_tem_registro(app_instance, monkeypatch):
    class ConnFalsa:
        @staticmethod
        def execute(query):
            class Res:
                @staticmethod
                def fetchone():
                    return ("96097c95c490",)

            return Res()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    class EngineFalso:
        @staticmethod
        def connect():
            return ConnFalsa()

    class DbFalso:
        engine = EngineFalso()

    monkeypatch.setattr(migracoes, "db", DbFalso())

    with app_instance.app_context():
        assert migracoes._historico_migracao_presente({"alembic_version"}) is True
