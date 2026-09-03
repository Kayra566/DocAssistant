import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    title: str
    body: str
    link: str | None
    read: bool
    created_at: datetime


class UnreadCountResponse(BaseModel):
    unread: int


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1)
    # Yanlışlıkla silmeyi önlemek için açık onay.
    confirm: bool


class DeleteAccountResponse(BaseModel):
    organizations_deleted: int
    files_deleted: int


class AuditVerifyResponse(BaseModel):
    valid: bool
    checked: int
    broken_at: str | None


class FeatureFlagsResponse(BaseModel):
    flags: list[str]
    environment: str
    default_locale: str
    sentry_enabled: bool
