import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from agent_runtime.api.dependencies import CurrentMember, DbSession
from agent_runtime.conversations import service
from agent_runtime.db.models import MessageRole

router = APIRouter(prefix="/conversations", tags=["conversations"])

MessageText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)
]


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)


class MessageCreate(BaseModel):
    content: MessageText


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime


class ConversationDetail(ConversationOut):
    messages: list[MessageOut]


def _not_found() -> HTTPException:
    # 404 rather than 403, so callers can't learn that another business's conversation exists.
    return HTTPException(status.HTTP_404_NOT_FOUND, detail="Conversation not found")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: ConversationCreate, member: CurrentMember, session: DbSession
) -> ConversationOut:
    conversation = await service.create_conversation(
        session,
        tenant_id=member.tenant.id,
        created_by_user_id=member.user.id,
        title=body.title,
    )
    return ConversationOut.model_validate(conversation)


@router.get("")
async def list_conversations(
    member: CurrentMember,
    session: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ConversationOut]:
    conversations = await service.list_conversations(
        session, tenant_id=member.tenant.id, limit=limit, offset=offset
    )
    return [ConversationOut.model_validate(c) for c in conversations]


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: uuid.UUID, member: CurrentMember, session: DbSession
) -> ConversationDetail:
    try:
        conversation = await service.get_conversation(
            session, tenant_id=member.tenant.id, conversation_id=conversation_id
        )
    except service.ConversationNotFound:
        raise _not_found() from None
    messages = await service.list_messages(
        session, tenant_id=member.tenant.id, conversation_id=conversation.id
    )
    return ConversationDetail(
        **ConversationOut.model_validate(conversation).model_dump(),
        messages=[MessageOut.model_validate(m) for m in messages],
    )


@router.post("/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
async def post_message(
    conversation_id: uuid.UUID, body: MessageCreate, member: CurrentMember, session: DbSession
) -> MessageOut:
    try:
        message = await service.add_user_message(
            session,
            tenant_id=member.tenant.id,
            conversation_id=conversation_id,
            content=body.content,
        )
    except service.ConversationNotFound:
        raise _not_found() from None
    return MessageOut.model_validate(message)
