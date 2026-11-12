import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agent_runtime.config import Settings


def test_live_returns_ok(client: TestClient) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_503_when_dependencies_are_down(client: TestClient) -> None:
    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "postgres": "error", "redis": "error"}


def test_settings_fail_when_required_values_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("DATABASE_URL", "REDIS_URL", "JWT_SECRET"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)  # type: ignore[call-arg]

    missing = {error["loc"][0] for error in exc_info.value.errors()}
    assert missing == {"database_url", "redis_url", "jwt_secret"}


def test_settings_reject_short_jwt_secret(settings: Settings) -> None:
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(
            _env_file=None,  # type: ignore[call-arg]
            database_url=settings.database_url,
            redis_url=settings.redis_url,
            jwt_secret="too-short",
        )
