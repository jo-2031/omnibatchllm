import os
import socket
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from alembic import command
from alembic.config import Config

from agent_runtime.config import Settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://agent:agent@localhost:55432/agent_runtime_test"
)
TEST_REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://localhost:56379/1")


def _require_reachable(url: str, name: str) -> None:
    parts = urlsplit(url)
    host, port = parts.hostname or "localhost", parts.port
    if port is None:
        raise ValueError(f"{name} URL must include a port: {url}")
    try:
        with socket.create_connection((host, port), timeout=1):
            pass
    except OSError:
        pytest.skip(f"{name} is not reachable at {host}:{port}; run `make up`")


@pytest.fixture(scope="session")
def integration_settings() -> Settings:
    _require_reachable(TEST_DATABASE_URL, "Postgres")
    _require_reachable(TEST_REDIS_URL, "Redis")

    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    alembic_config.attributes["configure_logger"] = False
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")

    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        environment="test",
        database_url=TEST_DATABASE_URL,
        redis_url=TEST_REDIS_URL,
    )


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
