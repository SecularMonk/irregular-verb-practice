from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Irregular Verb Practice API"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./irregular_verbs.db"
    frontend_origin: str = "http://localhost:5173"

    llm_api_key: Optional[str] = None
    llm_model: str = "gpt-4o-mini"
    ai_max_retries: int = 2

    session_cookie_name: str = "anon_user_id"
    session_cookie_max_age_seconds: int = 60 * 60 * 24 * 365
    session_cookie_secure: bool = False

    model_config = SettingsConfigDict(
        env_file=(str(PROJECT_ROOT / ".env"), str(BACKEND_ROOT / ".env")),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
