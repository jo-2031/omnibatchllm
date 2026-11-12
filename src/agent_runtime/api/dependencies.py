from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from agent_runtime.auth import service
from agent_runtime.auth.tokens import InvalidTokenError, decode_access_token
from agent_runtime.config import Settings
from agent_runtime.db.session import get_session


def get_app_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


AppSettings = Annotated[Settings, Depends(get_app_settings)]
DbSession = Annotated[AsyncSession, Depends(get_session)]

_bearer = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_member(
    settings: AppSettings,
    session: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> service.Member:
    if credentials is None:
        raise _unauthorized()
    try:
        claims = decode_access_token(credentials.credentials, settings)
    except InvalidTokenError:
        raise _unauthorized() from None

    # Re-checked on every request, so removing someone from a business takes effect immediately.
    member = await service.load_member(session, user_id=claims.user_id, tenant_id=claims.tenant_id)
    if member is None:
        raise _unauthorized()
    return member


CurrentMember = Annotated[service.Member, Depends(get_current_member)]
