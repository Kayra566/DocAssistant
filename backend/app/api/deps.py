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
        raise AuthError(code="error.auth.missing_header")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = security.decode_token(token)
    except Exception as exc:  # jwt errors
        raise AuthError(code="error.auth.invalid_token") from exc

    if payload.get("type") != "access":
        raise AuthError(code="error.auth.invalid_token")

    user = await db.get(User, uuid.UUID(payload["sub"]))
    if not user or not user.is_active:
        raise AuthError(code="error.auth.inactive_user")
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
            raise PermissionError(code="error.permission.not_member")
        if ROLE_LEVEL[m.role] < ROLE_LEVEL[minimum]:
            raise PermissionError(code="error.permission")
        return user

    return _dep


async def require_superuser(user: User = Depends(get_current_user)) -> User:
    """Platform yönetimi uçları yalnızca superuser'a açıktır."""
    if not user.is_superuser:
        raise PermissionError(code="error.permission.superuser_required")
    return user
