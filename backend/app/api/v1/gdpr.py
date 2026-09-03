import json

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import ValidationError
from app.models.user import User
from app.schemas.system import DeleteAccountRequest, DeleteAccountResponse
from app.services import gdpr

router = APIRouter(prefix="/gdpr", tags=["gdpr"])


@router.get("/export")
async def export_my_data(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Veri taşınabilirliği: kullanıcıya ait tüm veriyi JSON olarak indirir."""
    payload = await gdpr.export_user_data(db, user)
    body = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    return Response(
        content=body,
        media_type="application/json",
        headers={
            "Content-Disposition": 'attachment; filename="docassistant-export.json"'
        },
    )


@router.post("/delete-account", response_model=DeleteAccountResponse)
async def delete_my_account(
    payload: DeleteAccountRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unutulma hakkı: hesabı ve tek sahibi olunan organizasyonları siler."""
    if not payload.confirm:
        raise ValidationError("Silme işlemi için onay gerekli.")
    result = await gdpr.delete_account(db, user, payload.password)
    return DeleteAccountResponse(**result)
