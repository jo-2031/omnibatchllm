import asyncio
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from agent_runtime.auth.passwords import hash_password, verify_dummy_password, verify_password
from agent_runtime.db.models import Membership, Role, Tenant, User


class SignupConflict(Exception):
    message = "Email or business slug is already taken"


class EmailAlreadyRegistered(SignupConflict):
    message = "Email is already registered"


class TenantSlugTaken(SignupConflict):
    message = "Business slug is already taken"


class InvalidCredentials(Exception):
    pass


class TenantSelectionRequired(Exception):
    pass


@dataclass(frozen=True)
class Member:
    user: User
    tenant: Tenant
    role: Role


def normalize_email(email: str) -> str:
    return email.strip().lower()


async def signup(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str,
    tenant_name: str,
    tenant_slug: str,
) -> Member:
    email = normalize_email(email)
    if await session.scalar(select(User.id).where(User.email == email)):
        raise EmailAlreadyRegistered
    if await session.scalar(select(Tenant.id).where(Tenant.slug == tenant_slug)):
        raise TenantSlugTaken

    # Argon2 is deliberately slow; run it off the event loop so other requests aren't blocked.
    password_hash = await asyncio.to_thread(hash_password, password)

    tenant = Tenant(name=tenant_name, slug=tenant_slug)
    user = User(email=email, password_hash=password_hash, full_name=full_name)
    session.add_all([tenant, user])
    await session.flush()
    session.add(Membership(tenant_id=tenant.id, user_id=user.id, role=Role.OWNER))

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise SignupConflict from exc

    return Member(user=user, tenant=tenant, role=Role.OWNER)


async def authenticate(
    session: AsyncSession, *, email: str, password: str, tenant_slug: str | None
) -> Member:
    user = await session.scalar(select(User).where(User.email == normalize_email(email)))
    if user is None:
        await asyncio.to_thread(verify_dummy_password, password)
        raise InvalidCredentials
    if not await asyncio.to_thread(verify_password, user.password_hash, password):
        raise InvalidCredentials

    query = (
        select(Tenant, Membership.role)
        .join(Membership, Membership.tenant_id == Tenant.id)
        .where(Membership.user_id == user.id)
    )
    if tenant_slug is not None:
        query = query.where(Tenant.slug == tenant_slug)
    rows = (await session.execute(query)).all()

    if not rows:
        raise InvalidCredentials
    if len(rows) > 1:
        raise TenantSelectionRequired
    tenant, role = rows[0]
    return Member(user=user, tenant=tenant, role=role)


async def load_member(
    session: AsyncSession, *, user_id: uuid.UUID, tenant_id: uuid.UUID
) -> Member | None:
    row = (
        await session.execute(
            select(User, Tenant, Membership.role)
            .join(Membership, Membership.user_id == User.id)
            .join(Tenant, Tenant.id == Membership.tenant_id)
            .where(User.id == user_id, Tenant.id == tenant_id)
        )
    ).first()
    if row is None:
        return None
    user, tenant, role = row
    return Member(user=user, tenant=tenant, role=role)
