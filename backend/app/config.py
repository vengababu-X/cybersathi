"""Application settings. Everything defaults to a fully offline, key-free setup."""

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # .../backend
DATA_DIR = BASE_DIR / "data"
ARTIFACT_DIR = BASE_DIR / "app" / "ml" / "artifacts"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_NAME: str = "CyberSathi API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Local SQLite file — no database server to install.
    DATABASE_URL: str = f"sqlite:///{(BASE_DIR / 'cybersathi.db').as_posix()}"

    # Dev-only default; generate a real one for any shared deployment.
    SECRET_KEY: str = "cybersathi-local-dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    # Optional local LLM (Ollama). Off by default: the app is fully functional without it.
    ENABLE_LLM: bool = False
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"

    RATE_LIMIT_PER_MINUTE: int = 60

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalise_debug(cls, value: object) -> object:
        """Accept conventional deployment labels from host environments."""
        if isinstance(value, str):
            label = value.strip().lower()
            if label in {"release", "production", "prod"}:
                return False
            if label in {"development", "dev"}:
                return True
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
