from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.plans import plan_catalog
from app.core.config import settings
from app.core.time import ensure_utc, utcnow
from app.models.ai import AIJob
from app.models.billing import Subscription, UsageMetric
from app.models.collab import ShareLink
from app.models.document import Document
from app.models.enums import Plan
from app.models.organization import Membership, Organization
from app.models.user import User
from app.services import quota, usage


async def _scalar(db: AsyncSession, stmt) -> int:
    return int((await db.execute(stmt)).scalar_one())


def _empty_trend(days: int) -> dict[date, dict[str, int]]:
    today = utcnow().date()
    return {
        today - timedelta(days=offset): {"documents": 0, "ai_jobs": 0}
        for offset in range(days - 1, -1, -1)
    }


async def _trend(
    db: AsyncSession, org_id: uuid.UUID, days: int
) -> list[dict[str, object]]:
    """Günlük doküman/AI işlem sayıları.

    Tarih gruplaması Python tarafında yapılır; SQLite ve Postgres'te aynı sonucu verir.
    """
    since = utcnow() - timedelta(days=days - 1)
    buckets = _empty_trend(days)

    for model, key in ((Document, "documents"), (AIJob, "ai_jobs")):
        rows = (
            await db.execute(
                select(model.created_at).where(
                    model.organization_id == org_id, model.created_at >= since
                )
            )
        ).scalars()
        for created_at in rows:
            moment = ensure_utc(created_at)
            if moment is None:
                continue
            bucket = buckets.get(moment.date())
            if bucket is not None:
                bucket[key] += 1

    return [
        {"date": day.isoformat(), **counts} for day, counts in sorted(buckets.items())
    ]


async def _distribution(db: AsyncSession, column, org_column, org_id: uuid.UUID):
    rows = (
        await db.execute(
            select(column, func.count())
            .where(org_column == org_id)
            .group_by(column)
            .order_by(func.count().desc())
        )
    ).all()
    return [{"key": str(key), "count": int(count)} for key, count in rows]


async def org_stats(db: AsyncSession, org_id: uuid.UUID) -> dict[str, object]:
    org = await db.get(Organization, org_id)
    plan = org.plan if org else Plan.FREE
    spec = plan_catalog()[plan]

    subscription = (
        await db.execute(
            select(Subscription).where(Subscription.organization_id == org_id)
        )
    ).scalar_one_or_none()

    documents = await usage.document_count(db, org_id)
    storage_used = await usage.storage_bytes(db, org_id)

    return {
        "plan": plan,
        "subscription_status": str(subscription.status) if subscription else "active",
        "totals": {
            "documents": documents,
            "ai_jobs": await _scalar(
                db,
                select(func.count())
                .select_from(AIJob)
                .where(AIJob.organization_id == org_id),
            ),
            "share_links": await _scalar(
                db,
                select(func.count())
                .select_from(ShareLink)
                .where(
                    ShareLink.organization_id == org_id,
                    ShareLink.revoked.is_(False),
                ),
            ),
            "members": await _scalar(
                db,
                select(func.count())
                .select_from(Membership)
                .where(Membership.organization_id == org_id),
            ),
        },
        "quota": {
            "documents_used": documents,
            "documents_limit": spec.documents,
            "storage_bytes_used": storage_used,
            "storage_bytes_limit": quota.storage_limit_bytes(plan),
            "ai_requests_used": await usage.current(
                db, org_id, UsageMetric.AI_REQUESTS
            ),
            "ai_requests_limit": spec.ai_requests,
            "ai_tokens_used": await usage.current(db, org_id, UsageMetric.AI_TOKENS),
            "ai_tokens_limit": spec.ai_tokens,
        },
        "usage_trend": await _trend(db, org_id, settings.DASHBOARD_TREND_DAYS),
        "job_distribution": await _distribution(
            db, AIJob.type, AIJob.organization_id, org_id
        ),
        "document_status": await _distribution(
            db, Document.status, Document.organization_id, org_id
        ),
    }


async def platform_stats(db: AsyncSession) -> dict[str, object]:
    """Superuser paneli için platform geneli sayaçlar."""
    plan_rows = (
        await db.execute(
            select(Organization.plan, func.count()).group_by(Organization.plan)
        )
    ).all()

    return {
        "users": await _scalar(db, select(func.count()).select_from(User)),
        "verified_users": await _scalar(
            db,
            select(func.count()).select_from(User).where(User.is_verified.is_(True)),
        ),
        "organizations": await _scalar(
            db, select(func.count()).select_from(Organization)
        ),
        "documents": await _scalar(db, select(func.count()).select_from(Document)),
        "ai_jobs": await _scalar(db, select(func.count()).select_from(AIJob)),
        "share_links": await _scalar(db, select(func.count()).select_from(ShareLink)),
        "storage_bytes": int(
            (
                await db.execute(
                    select(func.coalesce(func.sum(Document.size_bytes), 0))
                )
            ).scalar_one()
        ),
        "plan_distribution": [
            {"key": str(plan), "count": int(count)} for plan, count in plan_rows
        ],
    }


async def platform_organizations(
    db: AsyncSession, limit: int = 50, offset: int = 0
) -> list[dict[str, object]]:
    doc_counts = (
        select(Document.organization_id, func.count().label("documents"))
        .group_by(Document.organization_id)
        .subquery()
    )
    member_counts = (
        select(Membership.organization_id, func.count().label("members"))
        .group_by(Membership.organization_id)
        .subquery()
    )
    rows = (
        await db.execute(
            select(
                Organization,
                func.coalesce(doc_counts.c.documents, 0),
                func.coalesce(member_counts.c.members, 0),
            )
            .outerjoin(doc_counts, doc_counts.c.organization_id == Organization.id)
            .outerjoin(
                member_counts, member_counts.c.organization_id == Organization.id
            )
            .order_by(Organization.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()

    return [
        {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "plan": org.plan,
            "documents": int(documents),
            "members": int(members),
            "created_at": org.created_at,
        }
        for org, documents, members in rows
    ]
