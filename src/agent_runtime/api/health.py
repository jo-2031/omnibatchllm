import asyncio
import logging

from fastapi import APIRouter, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

CHECK_TIMEOUT_SECONDS = 2.0


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request, response: Response) -> dict[str, str]:
    checks = {
        "postgres": await _check_postgres(request.app.state.db_engine),
        "redis": await _check_redis(request.app.state.redis),
    }
    healthy = all(result == "ok" for result in checks.values())
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if healthy else "unavailable", **checks}


async def _check_postgres(engine: AsyncEngine) -> str:
    try:
        async with asyncio.timeout(CHECK_TIMEOUT_SECONDS), engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        logger.warning("postgres readiness check failed", exc_info=True)
        return "error"
    return "ok"


async def _check_redis(redis: Redis) -> str:
    try:
        async with asyncio.timeout(CHECK_TIMEOUT_SECONDS):
            await redis.ping()
    except Exception:
        logger.warning("redis readiness check failed", exc_info=True)
        return "error"
    return "ok"
