import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agent_runtime.api.app import create_app
from agent_runtime.config import Settings


def test_live_returns_ok(client: TestClient) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_503_when_dependencies_are_down() -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        environment="test",
        database_url="postgresql+asyncpg://agent:agent@127.0.0.1:1/nothing",
        redis_url="redis://127.0.0.1:1/0",
    )

    with TestClient(create_app(settings)) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "postgres": "error", "redis": "error"}


def test_settings_fail_when_required_values_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)  # type: ignore[call-arg]

    missing = {error["loc"][0] for error in exc_info.value.errors()}
    assert missing == {"database_url", "redis_url"}
