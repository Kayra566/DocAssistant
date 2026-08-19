import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionError,
    ValidationError,
)
from app.core.time import ensure_utc, utcnow
from app.models.enums import ROLE_LEVEL, Role
from app.models.organization import Invitation, Membership, Organization
from app.models.user import User
from app.services.slug import unique_org_slug

INVITE_EXPIRE_DAYS = 7


def _now() -> datetime:
    return utcnow()


async def get_membership(
    db: AsyncSession, user_id: uuid.UUID, org_id: uuid.UUID
) -> Membership | None:
    return (
        await db.execute(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.organization_id == org_id,
            )
        )
    ).scalar_one_or_none()


async def _require_role(
    db: AsyncSession, user_id: uuid.UUID, org_id: uuid.UUID, minimum: Role
) -> Membership:
    m = await get_membership(db, user_id, org_id)
    if not m:
        raise PermissionError("Bu organizasyona üye değilsiniz.")
    if ROLE_LEVEL[m.role] < ROLE_LEVEL[minimum]:
        raise PermissionError("Bu işlem için yetkiniz yok.")
    return m


async def create_organization(
    db: AsyncSession, user: User, name: str
) -> Organization:
    org = Organization(name=name, slug=await unique_org_slug(db, name))
    db.add(org)
    await db.flush()
    db.add(Membership(user_id=user.id, organization_id=org.id, role=Role.OWNER))
    await db.commit()
    await db.refresh(org)
    return org


async def update_organization(
    db: AsyncSession, user: User, org_id: uuid.UUID, name: str
) -> Organization:
    await _require_role(db, user.id, org_id, Role.ADMIN)
    org = await db.get(Organization, org_id)
    if not org:
        raise NotFoundError("Organizasyon bulunamadı.")
    org.name = name
    await db.commit()
    await db.refresh(org)
    return org


async def list_members(
    db: AsyncSession, user: User, org_id: uuid.UUID
) -> list[tuple[Membership, User]]:
    await _require_role(db, user.id, org_id, Role.VIEWER)
    rows = (
        await db.execute(
            select(Membership, User)
            .join(User, User.id == Membership.user_id)
            .where(Membership.organization_id == org_id)
        )
    ).all()
    return [(m, u) for m, u in rows]


async def invite_member(
    db: AsyncSession, user: User, org_id: uuid.UUID, email: str, role: Role
) -> tuple[Invitation, str]:
    await _require_role(db, user.id, org_id, Role.ADMIN)
    if role == Role.OWNER:
        raise ValidationError("Owner rolüyle davet gönderilemez.")

    # Zaten üye mi?
    existing_user = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if existing_user and await get_membership(db, existing_user.id, org_id):
        raise ConflictError("Bu kullanıcı zaten organizasyon üyesi.")

    raw = security.generate_raw_token()
    invite = Invitation(
        organization_id=org_id,
        email=email,
        role=role,
        token_hash=security.hash_token(raw),
        invited_by=user.id,
        expires_at=_now() + timedelta(days=INVITE_EXPIRE_DAYS),
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return invite, raw


async def accept_invite(db: AsyncSession, user: User, raw_token: str) -> Membership:
    invite = (
        await db.execute(
            select(Invitation).where(
                Invitation.token_hash == security.hash_token(raw_token)
            )
        )
    ).scalar_one_or_none()
    if not invite or invite.accepted or ensure_utc(invite.expires_at) < _now():
        raise ValidationError("Davet geçersiz veya süresi dolmuş.")
    if invite.email.lower() != user.email.lower():
        raise PermissionError("Bu davet farklı bir email için gönderilmiş.")

    if await get_membership(db, user.id, invite.organization_id):
        invite.accepted = True
        await db.commit()
        raise ConflictError("Zaten bu organizasyonun üyesisiniz.")

    membership = Membership(
        user_id=user.id, organization_id=invite.organization_id, role=invite.role
    )
    db.add(membership)
    invite.accepted = True
    await db.commit()
    await db.refresh(membership)
    return membership


async def update_member_role(
    db: AsyncSession,
    user: User,
    org_id: uuid.UUID,
    target_user_id: uuid.UUID,
    new_role: Role,
) -> Membership:
    actor = await _require_role(db, user.id, org_id, Role.ADMIN)
    target = await get_membership(db, target_user_id, org_id)
    if not target:
        raise NotFoundError("Üye bulunamadı.")

    # Admin, Owner'ı değiştiremez ve Owner ataması yapamaz; bunu sadece Owner yapar.
    if (target.role == Role.OWNER or new_role == Role.OWNER) and actor.role != Role.OWNER:
        raise PermissionError("Owner rolünü yalnızca Owner değiştirebilir.")

    if target.role == Role.OWNER and new_role != Role.OWNER:
        await _ensure_not_last_owner(db, org_id, target_user_id)

    target.role = new_role
    await db.commit()
    await db.refresh(target)
    return target


async def remove_member(
    db: AsyncSession, user: User, org_id: uuid.UUID, target_user_id: uuid.UUID
) -> None:
    actor = await _require_role(db, user.id, org_id, Role.ADMIN)
    target = await get_membership(db, target_user_id, org_id)
    if not target:
        raise NotFoundError("Üye bulunamadı.")
    if target.role == Role.OWNER and actor.role != Role.OWNER:
        raise PermissionError("Owner yalnızca Owner tarafından çıkarılabilir.")
    if target.role == Role.OWNER:
        await _ensure_not_last_owner(db, org_id, target_user_id)
    await db.delete(target)
    await db.commit()


async def _ensure_not_last_owner(
    db: AsyncSession, org_id: uuid.UUID, excluding_user_id: uuid.UUID
) -> None:
    owners = (
        await db.execute(
            select(Membership).where(
                Membership.organization_id == org_id,
                Membership.role == Role.OWNER,
                Membership.user_id != excluding_user_id,
            )
        )
    ).scalars().all()
    if not owners:
        raise ValidationError("Organizasyonda en az bir Owner kalmalı.")


async def list_user_organizations(
    db: AsyncSession, user: User
) -> list[tuple[Organization, Role]]:
    rows = (
        await db.execute(
            select(Organization, Membership.role)
            .join(Membership, Membership.organization_id == Organization.id)
            .where(Membership.user_id == user.id)
        )
    ).all()
    return [(o, r) for o, r in rows]
