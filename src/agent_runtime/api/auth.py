import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from agent_runtime.api.dependencies import AppSettings, CurrentMember, DbSession
from agent_runtime.auth import service
from agent_runtime.auth.tokens import AccessTokenClaims, create_access_token
from agent_runtime.config import Settings
from agent_runtime.db.models import Role

router = APIRouter(tags=["auth"])

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)
    business_name: str = Field(min_length=1, max_length=200)
    business_slug: str = Field(min_length=3, max_length=63, pattern=SLUG_PATTERN)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)
    business_slug: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str


class TenantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str


class MeResponse(BaseModel):
    user: UserOut
    tenant: TenantOut
    role: Role


def _token_for(member: service.Member, settings: Settings) -> TokenResponse:
    claims = AccessTokenClaims(user_id=member.user.id, tenant_id=member.tenant.id)
    return TokenResponse(
        access_token=create_access_token(claims, settings),
        expires_in=settings.access_token_ttl_minutes * 60,
    )


@router.post("/auth/signup", status_code=status.HTTP_201_CREATED)
async def signup(body: SignupRequest, session: DbSession, settings: AppSettings) -> TokenResponse:
    try:
        member = await service.signup(
            session,
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            tenant_name=body.business_name,
            tenant_slug=body.business_slug,
        )
    except service.SignupConflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=exc.message) from None
    return _token_for(member, settings)


@router.post("/auth/login")
async def login(body: LoginRequest, session: DbSession, settings: AppSettings) -> TokenResponse:
    try:
        member = await service.authenticate(
            session, email=body.email, password=body.password, tenant_slug=body.business_slug
        )
    except service.InvalidCredentials:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        ) from None
    except service.TenantSelectionRequired:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="This account belongs to several businesses; send business_slug",
        ) from None
    return _token_for(member, settings)


@router.get("/me")
async def me(member: CurrentMember) -> MeResponse:
    return MeResponse(
        user=UserOut.model_validate(member.user),
        tenant=TenantOut.model_validate(member.tenant),
        role=member.role,
    )
