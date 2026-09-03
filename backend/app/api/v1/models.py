import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import registry
from app.ai.provider import reset_provider
from app.api.deps import get_current_user, require_role
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ValidationError
from app.models.enums import Role
from app.models.setting import ACTIVE_LLM
from app.models.user import User
from app.schemas.models import (
    ActiveModelResponse,
    ImportModelRequest,
    ModelInfoResponse,
    ModelListResponse,
    SetActiveModelRequest,
)
from app.services import app_settings

router = APIRouter(prefix="/models", tags=["models"])

require_owner = require_role(Role.OWNER)


async def _active(db: AsyncSession) -> ActiveModelResponse:
    value, _ = await app_settings.get(db, ACTIVE_LLM)
    model_id = (value or {}).get("model_id")
    if not model_id:
        # Ayar yapılmadıysa .env'deki yapılandırma geçerlidir.
        model_id = (
            f"ollama:{settings.OLLAMA_MODEL}"
            if settings.LLM_PROVIDER == "ollama"
            else "builtin:fake"
        )
    return ActiveModelResponse(model_id=model_id, configured=bool(value))


@router.get("", response_model=ModelListResponse)
async def list_models(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Klasöre bırakılan dosyaları ve Ollama modellerini birlikte listeler."""
    models = await registry.discover()
    active = await _active(db)
    return ModelListResponse(
        models=[ModelInfoResponse(**m.as_dict()) for m in models],
        active_model_id=active.model_id,
        models_dir=str(registry.models_dir()),
        ollama_available=await registry.ollama_available(),
    )


@router.get("/active", response_model=ActiveModelResponse)
async def active_model(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _active(db)


@router.put("/{org_id}/active", response_model=ActiveModelResponse)
async def set_active_model(
    org_id: uuid.UUID,
    payload: SetActiveModelRequest,
    user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Aktif modeli değiştirir; sonraki istekten itibaren geçerlidir."""
    available = {m.id for m in await registry.discover() if m.ready}
    if payload.model_id not in available:
        raise ValidationError(
            "Model kullanıma hazır değil. Dosya modellerini önce içe aktarın."
        )

    await app_settings.set_value(db, ACTIVE_LLM, {"model_id": payload.model_id})
    reset_provider()
    return await _active(db)


@router.post("/{org_id}/import", response_model=ModelInfoResponse)
async def import_model(
    org_id: uuid.UUID,
    payload: ImportModelRequest,
    user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Klasördeki bir .gguf dosyasını Ollama'ya kaydederek kullanılabilir yapar."""
    if not await registry.ollama_available():
        raise ValidationError(
            "Ollama çalışmıyor. Model dosyalarını kullanmak için Ollama'yı başlatın."
        )

    name = await registry.import_gguf(payload.filename)
    return ModelInfoResponse(
        id=f"ollama:{name}",
        name=name,
        source="ollama",
        ready=True,
        size_bytes=0,
        detail="İçe aktarıldı; artık seçilebilir.",
    )
