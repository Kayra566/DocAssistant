from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import UsageMetric, UsageRecord
from app.models.document import Document


def period_start(moment: datetime | None = None) -> datetime:
    """İçinde bulunulan aylık dönemin başlangıcı (kullanım sayaçları burada sıfırlanır)."""
    now = moment or datetime.now(UTC)
    return now.astimezone(UTC).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )


async def record(
    db: AsyncSession, org_id: uuid.UUID, metric: UsageMetric, amount: int
) -> None:
    """Aylık sayaca ekleme yapar. Commit çağıranın sorumluluğundadır."""
    if amount <= 0:
        return
    start = period_start()
    row = (
        await db.execute(
            select(UsageRecord).where(
                UsageRecord.organization_id == org_id,
                UsageRecord.period_start == start,
                UsageRecord.metric == metric,
            )
        )
    ).scalar_one_or_none()
    if row:
        row.value += amount
    else:
        db.add(
            UsageRecord(
                organization_id=org_id,
                period_start=start,
                metric=metric,
                value=amount,
            )
        )
    await db.flush()


async def current(db: AsyncSession, org_id: uuid.UUID, metric: UsageMetric) -> int:
    total = (
        await db.execute(
            select(func.coalesce(func.sum(UsageRecord.value), 0)).where(
                UsageRecord.organization_id == org_id,
                UsageRecord.period_start == period_start(),
                UsageRecord.metric == metric,
            )
        )
    ).scalar_one()
    return int(total)


async def document_count(db: AsyncSession, org_id: uuid.UUID) -> int:
    return int(
        (
            await db.execute(
                select(func.count())
                .select_from(Document)
                .where(Document.organization_id == org_id)
            )
        ).scalar_one()
    )


async def storage_bytes(db: AsyncSession, org_id: uuid.UUID) -> int:
    return int(
        (
            await db.execute(
                select(func.coalesce(func.sum(Document.size_bytes), 0)).where(
                    Document.organization_id == org_id
                )
            )
        ).scalar_one()
    )
