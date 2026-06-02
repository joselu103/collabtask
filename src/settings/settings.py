# src/settings.py
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.test"), env_file_encoding="utf-8", extra="ignore"
    )

    # App
    app_name: str = "CollabTask"
    app_version: str = "0.0.1"
    debug: bool = False
    host: str = "localhost"
    port: int = 8000
    allowed_origins: list[str] = ["*"]

    # Database
    database_url: SecretStr

    # Authentication
    secret_key: SecretStr
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Redis
    redis_url: SecretStr

    # Email:
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: SecretStr
    email_from: str
    smtp_tls: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
