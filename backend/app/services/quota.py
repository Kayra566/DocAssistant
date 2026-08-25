from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.models.ai import AIJob
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


def ai_token_limit(plan: Plan) -> int:
    return {
        Plan.FREE: settings.QUOTA_FREE_AI_TOKENS,
        Plan.PRO: settings.QUOTA_PRO_AI_TOKENS,
        Plan.BUSINESS: settings.QUOTA_BUSINESS_AI_TOKENS,
    }[plan]


async def month_token_usage(db: AsyncSession, org_id: uuid.UUID) -> int:
    start = datetime.now(UTC).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    total = (
        await db.execute(
            select(func.coalesce(func.sum(AIJob.tokens_used), 0)).where(
                AIJob.organization_id == org_id, AIJob.created_at >= start
            )
        )
    ).scalar_one()
    return int(total)


async def ensure_ai_quota(
    db: AsyncSession, org_id: uuid.UUID, estimated_tokens: int = 0
) -> None:
    org = await db.get(Organization, org_id)
    if not org:
        return
    used = await month_token_usage(db, org_id)
    limit = ai_token_limit(org.plan)
    if used + estimated_tokens > limit:
        raise QuotaExceededError(
            f"{org.plan} planı aylık AI token kotası aşıldı ({limit}). "
            "Planı yükseltin."
        )
