from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Ticketing LLM"
    database_url: str = "postgresql+asyncpg://ticketing:ticketing@localhost:5432/ticketing"

    llm_provider: Literal["openai", "anthropic"] = "anthropic"
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 2

    openai_api_key: str | None = None
    openai_model: str = "gpt-5"

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-opus-5-5"
    anthropic_effort: Literal["low", "medium", "high", "xhigh", "max"] = "low"
    anthropic_max_tokens: int = 4096


@lru_cache
def get_settings() -> Settings:
    return Settings()
