from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from agent_runtime.api.app import create_app
from agent_runtime.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        environment="test",
        database_url="postgresql+asyncpg://agent:agent@localhost:5432/agent_runtime_test",
        redis_url="redis://localhost:6379/1",
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as test_client:
        yield test_client
