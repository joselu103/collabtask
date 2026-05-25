# src/settings.py
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "CollabTask"
    app_version: str = "0.0.1"
    debug: bool = False
    host: str = "localhost"
    port: int = 8000
    allowed_origins: list[str] = ["*"]

    database_url: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
