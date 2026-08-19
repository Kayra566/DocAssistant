import uuid

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.database import get_db
from app.core.exceptions import AuthError, PermissionError
from app.models.enums import ROLE_LEVEL, Role
from app.models.user import User
from app.services.organization import get_membership


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError("Yetkilendirme başlığı eksik.")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = security.decode_token(token)
    except Exception as exc:  # jwt errors
        raise AuthError("Token geçersiz veya süresi dolmuş.") from exc

    if payload.get("type") != "access":
        raise AuthError("Geçersiz token türü.")

    user = await db.get(User, uuid.UUID(payload["sub"]))
    if not user or not user.is_active:
        raise AuthError("Kullanıcı bulunamadı veya pasif.")
    return user


def require_role(minimum: Role):
    """Belirli bir org için minimum rol gerektiren dependency üretir.

    Endpoint path'inde `org_id: uuid.UUID` parametresi bulunmalıdır.
    """

    async def _dep(
        org_id: uuid.UUID,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        m = await get_membership(db, user.id, org_id)
        if not m:
            raise PermissionError("Bu organizasyona üye değilsiniz.")
        if ROLE_LEVEL[m.role] < ROLE_LEVEL[minimum]:
            raise PermissionError("Bu işlem için yetkiniz yok.")
        return user

    return _dep
