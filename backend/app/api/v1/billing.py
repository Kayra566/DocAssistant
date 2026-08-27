import uuid

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.billing.plans import plan_catalog
from app.core.database import get_db
from app.models.enums import Role
from app.models.user import User
from app.schemas.billing import (
    BillingUsageResponse,
    CheckoutRequest,
    CheckoutResponse,
    PlanResponse,
    PortalResponse,
    SubscriptionResponse,
    WebhookAck,
)
from app.services import billing

router = APIRouter(prefix="/billing", tags=["billing"])

require_viewer = require_role(Role.VIEWER)
require_owner = require_role(Role.OWNER)


@router.get("/plans", response_model=list[PlanResponse])
async def plans() -> list[PlanResponse]:
    return [PlanResponse(**spec.__dict__) for spec in plan_catalog().values()]


@router.post("/webhook", response_model=WebhookAck)
async def webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
):
    payload = await request.body()
    result = await billing.handle_webhook(db, payload, stripe_signature)
    return WebhookAck(**result)


@router.get("/{org_id}/subscription", response_model=SubscriptionResponse)
async def subscription(
    org_id: uuid.UUID,
    user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
):
    return SubscriptionResponse.model_validate(
        await billing.get_subscription(db, org_id)
    )


@router.get("/{org_id}/usage", response_model=BillingUsageResponse)
async def usage(
    org_id: uuid.UUID,
    user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
):
    return BillingUsageResponse(**await billing.usage_summary(db, org_id))


@router.post("/{org_id}/checkout", response_model=CheckoutResponse)
async def checkout(
    org_id: uuid.UUID,
    payload: CheckoutRequest,
    user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await billing.start_checkout(
        db, org_id=org_id, plan=payload.plan, email=user.email
    )
    return CheckoutResponse(**result)


@router.post("/{org_id}/portal", response_model=PortalResponse)
async def portal(
    org_id: uuid.UUID,
    user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    return PortalResponse(**await billing.open_portal(db, org_id))
