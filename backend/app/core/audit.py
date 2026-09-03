"""Audit log değişmezliği: HMAC-SHA256 hash zinciri.

Her kayıt bir önceki kaydın imzasını da içerdiğinden, aradan bir satır silinir
veya değiştirilirse zincir doğrulaması bozulur.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.collab import ActivityLog

GENESIS = "0" * 64


def _payload(entry: ActivityLog, prev_signature: str) -> bytes:
    return json.dumps(
        {
            "id": str(entry.id),
            "organization_id": str(entry.organization_id),
            "user_id": str(entry.user_id) if entry.user_id else None,
            "action": entry.action,
            "resource_type": entry.resource_type,
            "resource_id": str(entry.resource_id) if entry.resource_id else None,
            "meta": entry.meta,
            "prev": prev_signature,
        },
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


def sign(entry: ActivityLog, prev_signature: str) -> str:
    return hmac.new(
        settings.JWT_SECRET.encode("utf-8"),
        _payload(entry, prev_signature),
        hashlib.sha256,
    ).hexdigest()


async def latest_signature(db: AsyncSession, org_id: uuid.UUID) -> str:
    row = (
        await db.execute(
            select(ActivityLog.signature)
            .where(
                ActivityLog.organization_id == org_id,
                ActivityLog.signature.is_not(None),
            )
            .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return row or GENESIS


async def verify_chain(db: AsyncSession, org_id: uuid.UUID) -> dict[str, object]:
    """Zinciri baştan sona doğrular ve ilk bozuk kaydı raporlar."""
    entries = list(
        (
            await db.execute(
                select(ActivityLog)
                .where(ActivityLog.organization_id == org_id)
                .order_by(ActivityLog.created_at.asc(), ActivityLog.id.asc())
            )
        )
        .scalars()
        .all()
    )

    previous = GENESIS
    for entry in entries:
        if entry.signature is None:
            continue
        if entry.prev_signature != previous or entry.signature != sign(entry, previous):
            return {
                "valid": False,
                "checked": len(entries),
                "broken_at": str(entry.id),
            }
        previous = entry.signature

    return {"valid": True, "checked": len(entries), "broken_at": None}
