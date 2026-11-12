from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, field_validator
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

    jwt_secret: SecretStr
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_ttl_minutes: int = 60

    @field_validator("jwt_secret")
    @classmethod
    def _jwt_secret_is_long_enough(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("must be at least 32 characters")
        return value


@lru_cache
def get_settings() -> Settings:
    # Raises ValidationError naming every missing or invalid variable.
    return Settings()
