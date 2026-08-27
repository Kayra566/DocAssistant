from __future__ import annotations

import asyncio
import uuid

from app.core.database import AsyncSessionLocal
from app.models.collab import ExportJob
from app.services.exports import run_export
from app.workers.celery_app import celery_app


async def _run(export_id: str) -> None:
    async with AsyncSessionLocal() as db:
        export = await db.get(ExportJob, uuid.UUID(export_id))
        if export:
            await run_export(db, export)


@celery_app.task(name="exports.run")
def run_export_task(export_id: str) -> None:
    asyncio.run(_run(export_id))
