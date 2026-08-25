from __future__ import annotations

import asyncio
import uuid

from app.core.database import AsyncSessionLocal
from app.models.document import Document
from app.services.documents import process_document
from app.workers.celery_app import celery_app


async def _run(document_id: str) -> None:
    async with AsyncSessionLocal() as db:
        doc = await db.get(Document, uuid.UUID(document_id))
        if doc:
            await process_document(db, doc)


@celery_app.task(name="documents.process")
def process_document_task(document_id: str) -> None:
    asyncio.run(_run(document_id))
