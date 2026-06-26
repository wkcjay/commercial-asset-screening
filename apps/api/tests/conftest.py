from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import PROJECT_ROOT, Settings
from app.db.engine import make_engine
from app.db.init_db import initialize_database
from app.main import create_app


@pytest.fixture()
def test_settings(tmp_path: Path) -> Settings:
    return Settings(
        sqlite_db_path=str(tmp_path / "local.db"),
        raw_data_dir=str(PROJECT_ROOT / "data" / "raw"),
        enable_ai_memo=False,
    )


@pytest.fixture()
def test_engine(test_settings: Settings):
    engine = make_engine(test_settings)
    initialize_database(engine, test_settings.raw_data_dir)
    return engine


@pytest.fixture()
def client(test_settings: Settings):
    app = create_app(test_settings)
    with TestClient(app) as test_client:
        yield test_client
