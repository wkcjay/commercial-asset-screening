from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.config import Settings


def make_engine(settings: Settings) -> Engine:
    db_path = Path(settings.sqlite_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    sqlite_url = f"sqlite:///{db_path.resolve().as_posix()}"
    return create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
        future=True,
    )
