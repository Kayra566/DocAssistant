from __future__ import annotations

import asyncio
import uuid

from app.core.database import AsyncSessionLocal
from app.models.ai import AIJob
from app.services.ai_features import run_job
from app.workers.celery_app import celery_app


async def _run(job_id: str) -> None:
    async with AsyncSessionLocal() as db:
        job = await db.get(AIJob, uuid.UUID(job_id))
        if job:
            await run_job(db, job)


@celery_app.task(name="ai.run_job")
def run_ai_job_task(job_id: str) -> None:
    asyncio.run(_run(job_id))
