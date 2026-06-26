from pathlib import Path

from app.config import get_settings
from app.db.engine import make_engine
from app.db.init_db import initialize_database


def main() -> None:
    settings = get_settings()
    db_path = Path(settings.sqlite_db_path)
    if db_path.exists():
        db_path.unlink()
    engine = make_engine(settings)
    version_id = initialize_database(engine, settings.raw_data_dir)
    print(f"Reset SQLite database at {settings.sqlite_db_path} with data version {version_id}")


if __name__ == "__main__":
    main()
