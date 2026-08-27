import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

ExportFormatLiteral = Literal["pdf", "docx", "xlsx", "md"]


class ExportCreate(BaseModel):
    ai_job_id: uuid.UUID
    format: ExportFormatLiteral = "pdf"


class ExportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ai_job_id: uuid.UUID
    format: ExportFormatLiteral
    status: str
    filename: str
    size_bytes: int
    error: str | None
    created_at: datetime
