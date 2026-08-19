import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.organization import (
    AcceptInviteRequest,
    InviteRequest,
    InviteResponse,
    MemberResponse,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    UpdateRoleRequest,
)
from app.services import organization as org_service

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=list[OrganizationResponse])
async def list_my_organizations(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    rows = await org_service.list_user_organizations(db, user)
    return [OrganizationResponse.model_validate(o) for o, _ in rows]


@router.post("", response_model=OrganizationResponse, status_code=201)
async def create_organization(
    payload: OrganizationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org = await org_service.create_organization(db, user, payload.name)
    return OrganizationResponse.model_validate(org)


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: uuid.UUID,
    payload: OrganizationUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org = await org_service.update_organization(db, user, org_id, payload.name)
    return OrganizationResponse.model_validate(org)


@router.get("/{org_id}/members", response_model=list[MemberResponse])
async def list_members(
    org_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await org_service.list_members(db, user, org_id)
    return [
        MemberResponse(
            user_id=u.id, email=u.email, full_name=u.full_name, role=m.role
        )
        for m, u in rows
    ]


@router.post("/{org_id}/invitations", response_model=InviteResponse, status_code=201)
async def invite_member(
    org_id: uuid.UUID,
    payload: InviteRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invite, raw = await org_service.invite_member(
        db, user, org_id, payload.email, payload.role
    )
    return InviteResponse(
        id=invite.id,
        email=invite.email,
        role=invite.role,
        dev_invite_token=raw if settings.EXPOSE_DEV_TOKENS else None,
    )


@router.post("/invitations/accept", response_model=MessageResponse)
async def accept_invitation(
    payload: AcceptInviteRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await org_service.accept_invite(db, user, payload.token)
    return MessageResponse(message="Davet kabul edildi.")


@router.patch("/{org_id}/members/{target_user_id}", response_model=MemberResponse)
async def update_member_role(
    org_id: uuid.UUID,
    target_user_id: uuid.UUID,
    payload: UpdateRoleRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    m = await org_service.update_member_role(
        db, user, org_id, target_user_id, payload.role
    )
    target = await db.get(User, target_user_id)
    return MemberResponse(
        user_id=target.id, email=target.email, full_name=target.full_name, role=m.role
    )


@router.delete("/{org_id}/members/{target_user_id}", response_model=MessageResponse)
async def remove_member(
    org_id: uuid.UUID,
    target_user_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await org_service.remove_member(db, user, org_id, target_user_id)
    return MessageResponse(message="Üye çıkarıldı.")
