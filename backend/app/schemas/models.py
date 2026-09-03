from pydantic import BaseModel, Field


class ModelInfoResponse(BaseModel):
    id: str
    name: str
    source: str
    ready: bool
    size_bytes: int
    detail: str


class ModelListResponse(BaseModel):
    models: list[ModelInfoResponse]
    active_model_id: str
    models_dir: str
    ollama_available: bool


class ActiveModelResponse(BaseModel):
    model_id: str
    # False ise .env varsayılanı kullanılıyor demektir.
    configured: bool


class SetActiveModelRequest(BaseModel):
    model_id: str = Field(min_length=1, max_length=200)


class ImportModelRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
