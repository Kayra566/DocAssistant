"""Çalışma zamanı ayarları — DB'de tutulur, süreçler arası versiyonla senkronlanır."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import AppSetting


async def get(db: AsyncSession, key: str) -> tuple[dict[str, Any] | None, int]:
    row = (
        await db.execute(select(AppSetting).where(AppSetting.key == key))
    ).scalar_one_or_none()
    return (row.value, row.version) if row else (None, 0)


async def set_value(
    db: AsyncSession, key: str, value: dict[str, Any]
) -> tuple[dict[str, Any], int]:
    row = (
        await db.execute(select(AppSetting).where(AppSetting.key == key))
    ).scalar_one_or_none()
    if row:
        row.value = value
        row.version += 1
    else:
        row = AppSetting(key=key, value=value, version=1)
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return row.value or {}, row.version
