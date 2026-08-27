import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

SharePermissionLiteral = Literal["view", "download"]


class ShareLinkCreate(BaseModel):
    document_id: uuid.UUID
    permission: SharePermissionLiteral = "view"
    email: EmailStr | None = None
    expires_in_hours: int | None = Field(default=None, ge=1, le=720)


class ShareLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    permission: SharePermissionLiteral
    email: str | None
    expires_at: datetime
    revoked: bool
    view_count: int
    last_accessed_at: datetime | None
    created_at: datetime


class ShareLinkCreated(ShareLinkResponse):
    """Ham token yalnızca oluşturma yanıtında döner."""

    token: str
    url: str


class SharedDocumentResponse(BaseModel):
    filename: str
    file_type: str
    size_bytes: int
    page_count: int
    permission: SharePermissionLiteral
    can_download: bool
    expires_at: datetime
    organization_name: str


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    page: int | None = Field(default=None, ge=0)


class CommentResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    page: int | None
    content: str
    author_email: str | None
    created_at: datetime


class ActivityResponse(BaseModel):
    id: uuid.UUID
    action: str
    resource_type: str
    resource_id: uuid.UUID | None
    meta: dict[str, Any] | None
    actor_email: str | None
    created_at: datetime
