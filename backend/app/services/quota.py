from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.models.document import Document
from app.models.enums import Plan
from app.models.organization import Organization


class QuotaExceededError(AppError):
    status_code = 402
    message = "Plan kotası aşıldı."


def document_limit(plan: Plan) -> int:
    return {
        Plan.FREE: settings.QUOTA_FREE_DOCUMENTS,
        Plan.PRO: settings.QUOTA_PRO_DOCUMENTS,
        Plan.BUSINESS: settings.QUOTA_BUSINESS_DOCUMENTS,
    }[plan]


async def ensure_document_quota(db: AsyncSession, org_id: uuid.UUID) -> None:
    org = await db.get(Organization, org_id)
    if not org:
        return
    count = (
        await db.execute(
            select(func.count())
            .select_from(Document)
            .where(Document.organization_id == org_id)
        )
    ).scalar_one()
    if count >= document_limit(org.plan):
        raise QuotaExceededError(
            f"{org.plan} planı doküman limitine ulaşıldı "
            f"({document_limit(org.plan)}). Planı yükseltin."
        )
