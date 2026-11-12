import uuid
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import SecretStr

from agent_runtime.auth.passwords import hash_password, verify_password
from agent_runtime.auth.tokens import (
    AccessTokenClaims,
    InvalidTokenError,
    create_access_token,
    decode_access_token,
)
from agent_runtime.config import Settings


def test_password_hash_verifies_only_the_right_password() -> None:
    password_hash = hash_password("correct horse battery")

    assert password_hash != "correct horse battery"
    assert verify_password(password_hash, "correct horse battery")
    assert not verify_password(password_hash, "wrong password")


def test_verify_password_rejects_a_malformed_hash() -> None:
    assert not verify_password("not-an-argon2-hash", "anything")


def test_token_round_trip(settings: Settings) -> None:
    claims = AccessTokenClaims(user_id=uuid.uuid4(), tenant_id=uuid.uuid4())

    token = create_access_token(claims, settings)

    assert decode_access_token(token, settings) == claims


def test_expired_token_is_rejected(settings: Settings) -> None:
    claims = AccessTokenClaims(user_id=uuid.uuid4(), tenant_id=uuid.uuid4())
    issued_long_ago = datetime.now(UTC) - timedelta(minutes=settings.access_token_ttl_minutes + 1)

    token = create_access_token(claims, settings, now=issued_long_ago)

    with pytest.raises(InvalidTokenError):
        decode_access_token(token, settings)


def test_token_signed_with_another_secret_is_rejected(settings: Settings) -> None:
    other = settings.model_copy(update={"jwt_secret": SecretStr("x" * 40)})
    claims = AccessTokenClaims(user_id=uuid.uuid4(), tenant_id=uuid.uuid4())

    token = create_access_token(claims, other)

    with pytest.raises(InvalidTokenError):
        decode_access_token(token, settings)


def test_garbage_token_is_rejected(settings: Settings) -> None:
    with pytest.raises(InvalidTokenError):
        decode_access_token("not.a.token", settings)
