import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

from agent_runtime.config import Settings


class InvalidTokenError(Exception):
    pass


@dataclass(frozen=True)
class AccessTokenClaims:
    user_id: uuid.UUID
    tenant_id: uuid.UUID


def create_access_token(
    claims: AccessTokenClaims, settings: Settings, *, now: datetime | None = None
) -> str:
    issued_at = now or datetime.now(UTC)
    payload = {
        "sub": str(claims.user_id),
        "tid": str(claims.tenant_id),
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=settings.access_token_ttl_minutes),
    }
    return jwt.encode(
        payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str, settings: Settings) -> AccessTokenClaims:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "tid", "iat", "exp"]},
        )
        return AccessTokenClaims(
            user_id=uuid.UUID(payload["sub"]), tenant_id=uuid.UUID(payload["tid"])
        )
    except (jwt.PyJWTError, ValueError) as exc:
        raise InvalidTokenError from exc
