import re
import secrets
import unicodedata

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization


def _base_slug(name: str) -> str:
    value = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "org"


async def unique_org_slug(db: AsyncSession, name: str) -> str:
    from sqlalchemy import select

    base = _base_slug(name)
    slug = base
    while True:
        exists = (
            await db.execute(select(Organization).where(Organization.slug == slug))
        ).scalar_one_or_none()
        if not exists:
            return slug
        slug = f"{base}-{secrets.token_hex(3)}"
