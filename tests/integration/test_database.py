import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from agent_runtime.api.app import create_app
from agent_runtime.config import Settings
from agent_runtime.db.models import Tenant
from agent_runtime.db.session import create_engine, create_session_factory

pytestmark = pytest.mark.integration


def test_ready_returns_ok_when_dependencies_are_up(integration_settings: Settings) -> None:
    with TestClient(create_app(integration_settings)) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "postgres": "ok", "redis": "ok"}


@pytest.mark.anyio
async def test_migrations_enable_pgvector(integration_settings: Settings) -> None:
    engine = create_engine(integration_settings.database_url)
    try:
        async with engine.connect() as connection:
            extension = await connection.scalar(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            )
    finally:
        await engine.dispose()

    assert extension == "vector"


@pytest.mark.anyio
async def test_tenant_round_trip(integration_settings: Settings) -> None:
    engine = create_engine(integration_settings.database_url)
    session_factory = create_session_factory(engine)
    slug = f"acme-{uuid.uuid4().hex[:8]}"
    try:
        async with session_factory() as session:
            tenant = Tenant(name="Acme", slug=slug)
            session.add(tenant)
            await session.commit()

        async with session_factory() as session:
            loaded = await session.get(Tenant, tenant.id)
    finally:
        await engine.dispose()

    assert loaded is not None
    assert loaded.slug == slug
    assert loaded.created_at is not None
