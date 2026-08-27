from __future__ import annotations

import asyncio

from app.core.database import AsyncSessionLocal
from app.services.billing import reconcile
from app.workers.celery_app import celery_app


async def _run() -> dict[str, int]:
    async with AsyncSessionLocal() as db:
        return await reconcile(db)


@celery_app.task(name="billing.reconcile")
def reconcile_subscriptions_task() -> dict[str, int]:
    """Günlük mutabakat: sağlayıcı durumunu senkronize eder."""
    return asyncio.run(_run())
