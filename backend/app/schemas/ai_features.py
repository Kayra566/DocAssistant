import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SummaryLevel = Literal["short", "detailed", "bullets", "executive"]
Preset = Literal["genel", "hukuk", "akademik", "is"]
QuizType = Literal["multiple_choice", "true_false", "open_ended"]


class _BaseTaskRequest(BaseModel):
    document_id: uuid.UUID
    preset: Preset = "genel"


class SummaryRequest(_BaseTaskRequest):
    level: SummaryLevel = "short"


class KeyPointsRequest(_BaseTaskRequest):
    pass


class QuizRequest(_BaseTaskRequest):
    question_count: int = Field(default=5, ge=1, le=20)
    question_types: list[QuizType] = Field(default_factory=lambda: ["multiple_choice"])


class TranslateRequest(_BaseTaskRequest):
    target_language: str = Field(min_length=2, max_length=40)
    source_language: str | None = Field(default=None, max_length=40)


class ExtractRequest(_BaseTaskRequest):
    schema_hint: str | None = Field(default=None, max_length=500)


class CompareRequest(_BaseTaskRequest):
    other_document_id: uuid.UUID


class AIJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID | None
    type: str
    status: str
    params: dict[str, Any] | None
    result: dict[str, Any] | None
    error: str | None
    tokens_used: int
    cache_hit: bool
    created_at: datetime


class PresetInfo(BaseModel):
    key: str
    description: str


class PromptPresetsResponse(BaseModel):
    presets: list[PresetInfo]
    summary_levels: list[PresetInfo]
