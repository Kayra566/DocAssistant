from __future__ import annotations

import re
import unicodedata
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.storage import get_storage
from app.exports.builder import JOB_TITLES, build_export_document
from app.exports.renderers import MIME_TYPES, render
from app.models.ai import AIJob, AIJobStatus
from app.models.collab import ExportFormat, ExportJob, ExportStatus
from app.models.document import Document
from app.services import activity

_UNSAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(name: str) -> str:
    """Content-Disposition başlığına güvenle konabilecek ASCII dosya adı üretir."""
    ascii_name = (
        unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    )
    cleaned = _UNSAFE_FILENAME.sub("-", ascii_name).strip("-._")
    return cleaned[:120] or "export"


def content_type(fmt: ExportFormat) -> str:
    return MIME_TYPES[fmt]


async def _load_job(db: AsyncSession, org_id: uuid.UUID, ai_job_id: uuid.UUID) -> AIJob:
    job = (
        await db.execute(
            select(AIJob).where(
                AIJob.id == ai_job_id, AIJob.organization_id == org_id
            )
        )
    ).scalar_one_or_none()
    if not job:
        raise NotFoundError("AI işlemi bulunamadı.")
    if job.status != AIJobStatus.DONE:
        raise ValidationError("Yalnızca tamamlanmış AI sonuçları dışa aktarılabilir.")
    return job


async def run_export(db: AsyncSession, export: ExportJob) -> ExportJob:
    """Export'u üretir ve depolamaya yazar. Hata durumunda FAILED işaretler."""
    export.status = ExportStatus.RUNNING
    await db.commit()
    try:
        job = await _load_job(db, export.organization_id, export.ai_job_id)
        document = await db.get(Document, job.document_id) if job.document_id else None
        payload = render(
            build_export_document(job, document.filename if document else "Doküman"),
            export.format,
        )
        storage_key = f"{export.organization_id}/exports/{export.id}.{export.format}"
        get_storage().put(storage_key, payload, content_type(export.format))

        export.storage_key = storage_key
        export.size_bytes = len(payload)
        export.status = ExportStatus.DONE
        export.error = None
        await db.commit()
    except Exception as exc:
        await db.rollback()
        export.status = ExportStatus.FAILED
        export.error = str(exc)[:2000]
        await db.commit()
    await db.refresh(export)
    return export


async def create_export(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    ai_job_id: uuid.UUID,
    fmt: ExportFormat,
) -> ExportJob:
    """Export kaydı oluşturur; eager modda hemen üretir, aksi halde kuyruğa atar."""
    job = await _load_job(db, org_id, ai_job_id)
    title = JOB_TITLES.get(str(job.type), str(job.type))

    export = ExportJob(
        organization_id=org_id,
        user_id=user_id,
        ai_job_id=job.id,
        format=fmt,
        status=ExportStatus.PENDING,
        filename=f"{safe_filename(title)}-{str(job.id)[:8]}.{fmt}",
    )
    db.add(export)
    await db.commit()
    await db.refresh(export)

    await activity.log(
        db,
        org_id=org_id,
        user_id=user_id,
        action=activity.EXPORT_CREATED,
        resource_type="ai_job",
        resource_id=job.id,
        meta={"format": str(fmt)},
    )

    if settings.EXPORTS_EAGER:
        return await run_export(db, export)

    from app.workers.export_tasks import run_export_task

    run_export_task.delay(str(export.id))
    return export


async def get_export(
    db: AsyncSession, org_id: uuid.UUID, export_id: uuid.UUID
) -> ExportJob:
    export = (
        await db.execute(
            select(ExportJob).where(
                ExportJob.id == export_id, ExportJob.organization_id == org_id
            )
        )
    ).scalar_one_or_none()
    if not export:
        raise NotFoundError("Export bulunamadı.")
    return export


async def list_exports(
    db: AsyncSession, org_id: uuid.UUID, ai_job_id: uuid.UUID | None = None
) -> list[ExportJob]:
    stmt = (
        select(ExportJob)
        .where(ExportJob.organization_id == org_id)
        .order_by(ExportJob.created_at.desc())
    )
    if ai_job_id:
        stmt = stmt.where(ExportJob.ai_job_id == ai_job_id)
    return list((await db.execute(stmt)).scalars().all())


async def read_export(
    db: AsyncSession, org_id: uuid.UUID, export_id: uuid.UUID
) -> tuple[ExportJob, bytes]:
    export = await get_export(db, org_id, export_id)
    if export.status != ExportStatus.DONE or not export.storage_key:
        raise ValidationError("Export henüz hazır değil.")
    return export, get_storage().get(export.storage_key)
