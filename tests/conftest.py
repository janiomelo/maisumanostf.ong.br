import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app


@pytest.fixture
def app_instance():
    app = create_app()
    app.config.update(TESTING=True)
    return app


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()
