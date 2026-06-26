from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    data_mode: str = "sqlite"
    sqlite_db_path: str = str(PROJECT_ROOT / "data" / "local.db")
    raw_data_dir: str = str(PROJECT_ROOT / "data" / "raw")
    ai_provider: str = "openai-compatible"
    ai_api_key: str | None = None
    ai_model: str | None = None
    ai_base_url: str | None = None
    enable_ai_memo: bool = False
    cors_allowed_origins: str = "http://localhost:3000"
    api_host: str = "127.0.0.1"
    api_port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()
