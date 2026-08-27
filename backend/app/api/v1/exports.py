import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.database import get_db
from app.models.collab import ExportFormat
from app.models.enums import Role
from app.models.user import User
from app.schemas.exports import ExportCreate, ExportResponse
from app.services import exports as export_service

router = APIRouter(prefix="/exports", tags=["exports"])

require_viewer = require_role(Role.VIEWER)
require_member = require_role(Role.MEMBER)


@router.post("/{org_id}", response_model=ExportResponse, status_code=201)
async def create_export(
    org_id: uuid.UUID,
    payload: ExportCreate,
    user: User = Depends(require_member),
    db: AsyncSession = Depends(get_db),
):
    export = await export_service.create_export(
        db,
        org_id=org_id,
        user_id=user.id,
        ai_job_id=payload.ai_job_id,
        fmt=ExportFormat(payload.format),
    )
    return ExportResponse.model_validate(export)


@router.get("/{org_id}", response_model=list[ExportResponse])
async def list_exports(
    org_id: uuid.UUID,
    ai_job_id: uuid.UUID | None = Query(default=None),
    user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
):
    rows = await export_service.list_exports(db, org_id, ai_job_id)
    return [ExportResponse.model_validate(row) for row in rows]


@router.get("/{org_id}/{export_id}", response_model=ExportResponse)
async def get_export(
    org_id: uuid.UUID,
    export_id: uuid.UUID,
    user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
):
    return ExportResponse.model_validate(
        await export_service.get_export(db, org_id, export_id)
    )


@router.get("/{org_id}/{export_id}/download")
async def download_export(
    org_id: uuid.UUID,
    export_id: uuid.UUID,
    user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
):
    export, payload = await export_service.read_export(db, org_id, export_id)
    return Response(
        content=payload,
        media_type=export_service.content_type(export.format),
        headers={
            "Content-Disposition": f'attachment; filename="{export.filename}"',
        },
    )
