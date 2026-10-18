from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SwarVox AI"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "local-development-only-change-me"
    webhook_secret: str = "local-development-only-webhook-secret"
    database_url: str = "sqlite:///./swarvox.db"
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    telephony_provider: str = "mock"
    default_caller_id: str = "+910000000000"

    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[2] / ".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @property
    def is_local(self) -> bool:
        return self.environment.lower() in {"local", "dev", "development", "test"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
