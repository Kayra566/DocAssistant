import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import Plan, Role


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class OrganizationUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    plan: Plan
    created_at: datetime


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role: Role


class InviteRequest(BaseModel):
    email: EmailStr
    role: Role = Role.MEMBER


class InviteResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: Role
    dev_invite_token: str | None = None


class AcceptInviteRequest(BaseModel):
    token: str


class UpdateRoleRequest(BaseModel):
    role: Role
