import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app


@pytest.fixture
def app_instance(tmp_path):
    banco_teste = tmp_path / "test.db"
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{banco_teste}",
        }
    )
    return app


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()
