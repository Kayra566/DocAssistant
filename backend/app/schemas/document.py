import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    file_type: str
    mime_type: str
    size_bytes: int
    status: DocumentStatus
    error: str | None
    page_count: int
    chunk_count: int
    is_favorite: bool
    created_at: datetime


class DocumentDownloadResponse(BaseModel):
    url: str
    expires_in_minutes: int


class FavoriteRequest(BaseModel):
    is_favorite: bool


class BatchUploadResult(BaseModel):
    uploaded: list[DocumentResponse]
    errors: list[dict[str, str]]
