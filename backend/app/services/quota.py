from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.plans import get_plan
from app.core.exceptions import AppError
from app.models.billing import UsageMetric
from app.models.enums import Plan
from app.models.organization import Organization
from app.services import usage

MB = 1024 * 1024


class QuotaExceededError(AppError):
    status_code = 402
    message = "Plan kotası aşıldı."
    code = "error.quota"


def document_limit(plan: Plan) -> int:
    return get_plan(plan).documents


def storage_limit_bytes(plan: Plan) -> int:
    return get_plan(plan).storage_mb * MB


def ai_token_limit(plan: Plan) -> int:
    return get_plan(plan).ai_tokens


def ai_request_limit(plan: Plan) -> int:
    return get_plan(plan).ai_requests


async def _plan_of(db: AsyncSession, org_id: uuid.UUID) -> Plan | None:
    org = await db.get(Organization, org_id)
    return org.plan if org else None


async def ensure_document_quota(
    db: AsyncSession, org_id: uuid.UUID, incoming_bytes: int = 0
) -> None:
    plan = await _plan_of(db, org_id)
    if plan is None:
        return

    count = await usage.document_count(db, org_id)
    if count >= document_limit(plan):
        raise QuotaExceededError(
            f"{plan} planı doküman limitine ulaşıldı ({document_limit(plan)}). "
            "Planı yükseltin."
        )

    stored = await usage.storage_bytes(db, org_id)
    limit = storage_limit_bytes(plan)
    if stored + incoming_bytes > limit:
        raise QuotaExceededError(
            f"{plan} planı depolama limiti aşıldı ({limit // MB} MB). Planı yükseltin."
        )


async def month_token_usage(db: AsyncSession, org_id: uuid.UUID) -> int:
    return await usage.current(db, org_id, UsageMetric.AI_TOKENS)


async def month_request_usage(db: AsyncSession, org_id: uuid.UUID) -> int:
    return await usage.current(db, org_id, UsageMetric.AI_REQUESTS)


async def ensure_ai_quota(
    db: AsyncSession, org_id: uuid.UUID, estimated_tokens: int = 0
) -> None:
    plan = await _plan_of(db, org_id)
    if plan is None:
        return

    requests = await month_request_usage(db, org_id)
    if requests >= ai_request_limit(plan):
        raise QuotaExceededError(
            f"{plan} planı aylık AI istek kotası aşıldı ({ai_request_limit(plan)}). "
            "Planı yükseltin."
        )

    tokens = await month_token_usage(db, org_id)
    limit = ai_token_limit(plan)
    if tokens + estimated_tokens > limit:
        raise QuotaExceededError(
            f"{plan} planı aylık AI token kotası aşıldı ({limit}). Planı yükseltin."
        )
