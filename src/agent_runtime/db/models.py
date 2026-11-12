import uuid
from enum import StrEnum

from sqlalchemy import CheckConstraint, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from agent_runtime.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    AGENT = "agent"


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(63), unique=True)


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(200))


class Membership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_memberships_tenant_id_user_id"),
        CheckConstraint("role IN ('owner', 'admin', 'agent')", name="role_valid"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[Role] = mapped_column(
        Enum(
            Role,
            native_enum=False,
            length=20,
            values_callable=lambda roles: [role.value for role in roles],
        )
    )
