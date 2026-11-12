import uuid
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration

NewBusiness = Callable[[], dict[str, str]]


def _create(api: TestClient, headers: dict[str, str], title: str | None = None) -> str:
    response = api.post("/conversations", json={"title": title}, headers=headers)
    assert response.status_code == 201, response.text
    conversation_id: str = response.json()["id"]
    return conversation_id


def test_create_and_read_conversation_with_messages_in_order(
    api: TestClient, new_business: NewBusiness
) -> None:
    owner = new_business()
    conversation_id = _create(api, owner, title="Order question")

    for text in ("first", "second", "third"):
        response = api.post(
            f"/conversations/{conversation_id}/messages", json={"content": text}, headers=owner
        )
        assert response.status_code == 201
        assert response.json()["role"] == "user"

    detail = api.get(f"/conversations/{conversation_id}", headers=owner).json()

    assert detail["title"] == "Order question"
    assert [m["content"] for m in detail["messages"]] == ["first", "second", "third"]


def test_list_shows_most_recently_active_first(api: TestClient, new_business: NewBusiness) -> None:
    owner = new_business()
    older = _create(api, owner, title="older")
    newer = _create(api, owner, title="newer")

    api.post(f"/conversations/{older}/messages", json={"content": "bump"}, headers=owner)
    listed = api.get("/conversations", headers=owner).json()

    assert [c["id"] for c in listed] == [older, newer]


def test_list_is_paginated(api: TestClient, new_business: NewBusiness) -> None:
    owner = new_business()
    for _ in range(3):
        _create(api, owner)

    first_page = api.get("/conversations", params={"limit": 2}, headers=owner).json()
    second_page = api.get("/conversations", params={"limit": 2, "offset": 2}, headers=owner).json()

    assert len(first_page) == 2
    assert len(second_page) == 1
    assert api.get("/conversations", params={"limit": 500}, headers=owner).status_code == 422


def test_businesses_cannot_see_or_write_each_others_conversations(
    api: TestClient, new_business: NewBusiness
) -> None:
    business_a = new_business()
    business_b = new_business()
    a_conversation = _create(api, business_a, title="private to A")

    read = api.get(f"/conversations/{a_conversation}", headers=business_b)
    write = api.post(
        f"/conversations/{a_conversation}/messages",
        json={"content": "sneaky"},
        headers=business_b,
    )
    b_list = api.get("/conversations", headers=business_b).json()

    assert read.status_code == 404
    assert write.status_code == 404
    assert b_list == []
    a_messages = api.get(f"/conversations/{a_conversation}", headers=business_a).json()
    assert a_messages["messages"] == []


def test_unknown_conversation_is_404(api: TestClient, new_business: NewBusiness) -> None:
    owner = new_business()

    assert api.get(f"/conversations/{uuid.uuid4()}", headers=owner).status_code == 404


@pytest.mark.parametrize("content", ["", "   ", "x" * 4001])
def test_message_content_is_validated(
    api: TestClient, new_business: NewBusiness, content: str
) -> None:
    owner = new_business()
    conversation_id = _create(api, owner)

    response = api.post(
        f"/conversations/{conversation_id}/messages", json={"content": content}, headers=owner
    )

    assert response.status_code == 422


def test_conversations_require_login(api: TestClient) -> None:
    assert api.get("/conversations").status_code == 401
    assert api.post("/conversations", json={}).status_code == 401
