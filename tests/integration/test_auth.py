import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

from agent_runtime.auth.tokens import AccessTokenClaims, create_access_token
from agent_runtime.config import Settings

pytestmark = pytest.mark.integration

PASSWORD = "a-long-enough-password"


def _signup(api: TestClient, **overrides: str) -> tuple[dict[str, Any], dict[str, str]]:
    suffix = uuid.uuid4().hex[:8]
    body = {
        "email": f"owner-{suffix}@example.com",
        "password": PASSWORD,
        "full_name": "Ada Owner",
        "business_name": f"Acme {suffix}",
        "business_slug": f"acme-{suffix}",
        **overrides,
    }
    response = api.post("/auth/signup", json=body)
    assert response.status_code == 201, response.text
    return response.json(), body


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_signup_creates_owner_and_me_returns_them(api: TestClient) -> None:
    tokens, body = _signup(api)

    response = api.get("/me", headers=_auth(tokens["access_token"]))

    assert response.status_code == 200
    me = response.json()
    assert me["user"]["email"] == body["email"]
    assert me["tenant"]["slug"] == body["business_slug"]
    assert me["role"] == "owner"
    assert "password_hash" not in me["user"]


def test_signup_rejects_duplicate_email_and_slug(api: TestClient) -> None:
    _, body = _signup(api)

    same_email = api.post(
        "/auth/signup", json={**body, "business_slug": f"other-{uuid.uuid4().hex[:8]}"}
    )
    same_slug = api.post(
        "/auth/signup", json={**body, "email": f"other-{uuid.uuid4().hex[:8]}@example.com"}
    )

    assert same_email.status_code == 409
    assert same_email.json()["detail"] == "Email is already registered"
    assert same_slug.status_code == 409
    assert same_slug.json()["detail"] == "Business slug is already taken"


def test_email_is_case_insensitive(api: TestClient) -> None:
    _, body = _signup(api)

    response = api.post("/auth/login", json={"email": body["email"].upper(), "password": PASSWORD})

    assert response.status_code == 200


def test_login_returns_token_that_works(api: TestClient) -> None:
    _, body = _signup(api)

    response = api.post("/auth/login", json={"email": body["email"], "password": PASSWORD})

    assert response.status_code == 200
    me = api.get("/me", headers=_auth(response.json()["access_token"]))
    assert me.json()["tenant"]["slug"] == body["business_slug"]


def test_login_with_wrong_password_or_unknown_email_gives_same_error(api: TestClient) -> None:
    _, body = _signup(api)

    wrong_password = api.post(
        "/auth/login", json={"email": body["email"], "password": "not-the-password"}
    )
    unknown_email = api.post(
        "/auth/login", json={"email": "nobody@example.com", "password": PASSWORD}
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_me_requires_a_valid_token(api: TestClient) -> None:
    assert api.get("/me").status_code == 401
    assert api.get("/me", headers=_auth("garbage")).status_code == 401


def test_cannot_log_in_to_another_business(api: TestClient) -> None:
    _, owner_a = _signup(api)
    _, owner_b = _signup(api)

    response = api.post(
        "/auth/login",
        json={
            "email": owner_a["email"],
            "password": PASSWORD,
            "business_slug": owner_b["business_slug"],
        },
    )

    assert response.status_code == 401


def test_token_for_a_business_you_dont_belong_to_is_rejected(
    api: TestClient, integration_settings: Settings
) -> None:
    tokens_a, _ = _signup(api)
    tokens_b, _ = _signup(api)
    user_a = api.get("/me", headers=_auth(tokens_a["access_token"])).json()["user"]
    tenant_b = api.get("/me", headers=_auth(tokens_b["access_token"])).json()["tenant"]

    # A correctly signed token claiming user A belongs to business B.
    forged = create_access_token(
        AccessTokenClaims(user_id=uuid.UUID(user_a["id"]), tenant_id=uuid.UUID(tenant_b["id"])),
        integration_settings,
    )

    assert api.get("/me", headers=_auth(forged)).status_code == 401


@pytest.mark.parametrize(
    "overrides",
    [
        {"password": "short"},
        {"email": "not-an-email"},
        {"business_slug": "Has Spaces"},
        {"business_slug": "-leading-dash"},
    ],
)
def test_signup_validates_input(api: TestClient, overrides: dict[str, str]) -> None:
    body = {
        "email": "valid@example.com",
        "password": PASSWORD,
        "full_name": "Ada",
        "business_name": "Acme",
        "business_slug": "acme-valid",
        **overrides,
    }

    assert api.post("/auth/signup", json=body).status_code == 422
