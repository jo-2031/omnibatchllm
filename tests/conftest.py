from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from agent_runtime.api.app import create_app
from agent_runtime.config import Settings

TEST_JWT_SECRET = "test-only-jwt-secret-that-is-long-enough"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        environment="test",
        database_url="postgresql+asyncpg://agent:agent@127.0.0.1:1/nothing",
        redis_url="redis://127.0.0.1:1/0",
        jwt_secret=TEST_JWT_SECRET,
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as test_client:
        yield test_client
