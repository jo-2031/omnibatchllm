import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from agent_runtime.api import auth, health
from agent_runtime.config import Settings, get_settings
from agent_runtime.db.session import create_engine, create_session_factory
from agent_runtime.observability import configure_logging
from agent_runtime.redis_client import create_redis

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(settings.database_url)
        redis = create_redis(settings.redis_url)
        app.state.db_engine = engine
        app.state.session_factory = create_session_factory(engine)
        app.state.redis = redis
        logger.info("api starting", extra={"environment": settings.environment})
        try:
            yield
        finally:
            await redis.aclose()
            await engine.dispose()
            logger.info("api stopping")

    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.include_router(health.router)
    app.include_router(auth.router)
    return app
