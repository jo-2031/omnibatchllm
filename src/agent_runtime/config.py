from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "agent-runtime"
    environment: Literal["local", "test", "staging", "production"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    api_host: str = "127.0.0.1"
    api_port: int = 8000

    database_url: str
    redis_url: str


@lru_cache
def get_settings() -> Settings:
    # Raises ValidationError naming every missing or invalid variable.
    return Settings()
