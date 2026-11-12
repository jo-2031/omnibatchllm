import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_runtime.db.models import Conversation, Message, MessageRole

# Every function takes tenant_id and filters by it, so one business can never read or write
# another's conversations, even with a valid conversation id.


class ConversationNotFound(Exception):
    pass


async def create_conversation(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    created_by_user_id: uuid.UUID | None,
    title: str | None,
) -> Conversation:
    conversation = Conversation(
        tenant_id=tenant_id, created_by_user_id=created_by_user_id, title=title
    )
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def list_conversations(
    session: AsyncSession, *, tenant_id: uuid.UUID, limit: int, offset: int
) -> Sequence[Conversation]:
    result = await session.scalars(
        select(Conversation)
        .where(Conversation.tenant_id == tenant_id)
        .order_by(Conversation.updated_at.desc(), Conversation.id)
        .limit(limit)
        .offset(offset)
    )
    return result.all()


async def get_conversation(
    session: AsyncSession, *, tenant_id: uuid.UUID, conversation_id: uuid.UUID
) -> Conversation:
    conversation = await session.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.tenant_id == tenant_id
        )
    )
    if conversation is None:
        raise ConversationNotFound
    return conversation


async def list_messages(
    session: AsyncSession, *, tenant_id: uuid.UUID, conversation_id: uuid.UUID
) -> Sequence[Message]:
    result = await session.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id, Message.tenant_id == tenant_id)
        .order_by(Message.seq)
    )
    return result.all()


async def add_user_message(
    session: AsyncSession, *, tenant_id: uuid.UUID, conversation_id: uuid.UUID, content: str
) -> Message:
    conversation = await get_conversation(
        session, tenant_id=tenant_id, conversation_id=conversation_id
    )
    message = Message(
        tenant_id=tenant_id,
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=content,
    )
    session.add(message)
    conversation.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(message)
    return message
