from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.gateway import get_gateway
from app.billing.plans import plan_catalog, plan_for_price_id
from app.core.exceptions import NotFoundError, ValidationError
from app.core.time import ensure_utc, utcnow
from app.models.billing import Subscription, SubscriptionStatus, UsageMetric, WebhookEvent
from app.models.enums import Plan
from app.models.organization import Organization
from app.services import quota, usage

HANDLED_EVENTS = {
    "checkout.session.completed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.payment_failed",
}


async def get_subscription(db: AsyncSession, org_id: uuid.UUID) -> Subscription:
    """Organizasyonun aboneliğini döndürür; yoksa Free abonelik oluşturur."""
    sub = (
        await db.execute(
            select(Subscription).where(Subscription.organization_id == org_id)
        )
    ).scalar_one_or_none()
    if sub:
        return sub

    org = await db.get(Organization, org_id)
    if not org:
        raise NotFoundError("Organizasyon bulunamadı.")
    sub = Subscription(
        organization_id=org_id,
        plan=org.plan,
        status=SubscriptionStatus.ACTIVE,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


async def start_checkout(
    db: AsyncSession, *, org_id: uuid.UUID, plan: Plan, email: str
) -> dict[str, Any]:
    if plan == Plan.FREE:
        raise ValidationError("Free plan için ödeme gerekmez.")
    sub = await get_subscription(db, org_id)
    session = get_gateway().create_checkout_session(
        org_id=org_id,
        plan=plan,
        customer_id=sub.provider_customer_id,
        email=email,
    )
    if session.get("customer") and not sub.provider_customer_id:
        sub.provider_customer_id = str(session["customer"])
        await db.commit()
    return {"session_id": session["id"], "url": session["url"]}


async def open_portal(db: AsyncSession, org_id: uuid.UUID) -> dict[str, Any]:
    sub = await get_subscription(db, org_id)
    if not sub.provider_customer_id:
        raise ValidationError("Bu organizasyon için ödeme müşterisi bulunmuyor.")
    session = get_gateway().create_portal_session(
        customer_id=sub.provider_customer_id
    )
    return {"url": session["url"]}


def _to_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, int | float):
        return datetime.fromtimestamp(float(value), tz=UTC)
    if isinstance(value, str):
        try:
            return ensure_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
        except ValueError:
            return None
    return None


def _plan_from_object(obj: dict[str, Any]) -> Plan | None:
    metadata = obj.get("metadata") or {}
    if metadata.get("plan"):
        try:
            return Plan(metadata["plan"])
        except ValueError:
            return None
    items = (obj.get("items") or {}).get("data") or []
    if items:
        price = (items[0] or {}).get("price") or {}
        if price.get("id"):
            return plan_for_price_id(str(price["id"]))
    return None


async def _resolve_subscription(
    db: AsyncSession, obj: dict[str, Any]
) -> Subscription | None:
    metadata = obj.get("metadata") or {}
    org_raw = metadata.get("organization_id") or obj.get("client_reference_id")
    if org_raw:
        try:
            return await get_subscription(db, uuid.UUID(str(org_raw)))
        except (ValueError, NotFoundError):
            return None

    for column, key in (
        (Subscription.provider_subscription_id, "id"),
        (Subscription.provider_customer_id, "customer"),
    ):
        value = obj.get(key)
        if value:
            found = (
                await db.execute(select(Subscription).where(column == str(value)))
            ).scalar_one_or_none()
            if found:
                return found
    return None


async def _apply_event(db: AsyncSession, event: dict[str, Any]) -> str:
    event_type = str(event["type"])
    obj = ((event.get("data") or {}).get("object")) or {}
    sub = await _resolve_subscription(db, obj)
    if not sub:
        return "ignored"

    if event_type == "checkout.session.completed":
        if obj.get("customer"):
            sub.provider_customer_id = str(obj["customer"])
        if obj.get("subscription"):
            sub.provider_subscription_id = str(obj["subscription"])
        plan = _plan_from_object(obj)
        if plan:
            sub.plan = plan
        sub.status = SubscriptionStatus.ACTIVE
        sub.cancel_at_period_end = False
    elif event_type in {
        "customer.subscription.created",
        "customer.subscription.updated",
    }:
        if obj.get("id"):
            sub.provider_subscription_id = str(obj["id"])
        if obj.get("customer"):
            sub.provider_customer_id = str(obj["customer"])
        plan = _plan_from_object(obj)
        if plan:
            sub.plan = plan
        raw_status = str(obj.get("status") or SubscriptionStatus.ACTIVE)
        sub.status = (
            SubscriptionStatus(raw_status)
            if raw_status in set(SubscriptionStatus)
            else SubscriptionStatus.ACTIVE
        )
        sub.cancel_at_period_end = bool(obj.get("cancel_at_period_end", False))
        sub.current_period_end = _to_datetime(obj.get("current_period_end"))
    elif event_type == "customer.subscription.deleted":
        sub.status = SubscriptionStatus.CANCELED
        sub.cancel_at_period_end = False
        sub.current_period_end = _to_datetime(obj.get("current_period_end"))
        sub.plan = Plan.FREE
    elif event_type == "invoice.payment_failed":
        sub.status = SubscriptionStatus.PAST_DUE
    else:
        return "ignored"

    await _sync_org_plan(db, sub)
    return "applied"


async def _sync_org_plan(db: AsyncSession, sub: Subscription) -> None:
    """Aktif olmayan abonelikte organizasyon Free'ye düşer."""
    org = await db.get(Organization, sub.organization_id)
    if not org:
        return
    effective = (
        sub.plan
        if sub.status in {SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING}
        else Plan.FREE
    )
    org.plan = effective


async def handle_webhook(
    db: AsyncSession, payload: bytes, signature: str | None
) -> dict[str, str]:
    """İmzayı doğrular, event'i tek kez işler (idempotent)."""
    event = get_gateway().parse_event(payload, signature)
    event_id = str(event["id"])

    existing = (
        await db.execute(select(WebhookEvent).where(WebhookEvent.event_id == event_id))
    ).scalar_one_or_none()
    if existing:
        return {"status": "duplicate", "event_id": event_id}

    log = WebhookEvent(event_id=event_id, type=str(event["type"]), payload=event)
    db.add(log)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        return {"status": "duplicate", "event_id": event_id}

    try:
        outcome = await _apply_event(db, event)
        log.processed_at = utcnow()
    except Exception as exc:
        log.error = str(exc)[:1000]
        log.processed_at = utcnow()
        await db.commit()
        raise
    await db.commit()
    return {"status": outcome, "event_id": event_id}


async def reconcile(db: AsyncSession) -> dict[str, int]:
    """Sağlayıcı durumunu senkronize eder ve süresi geçen abonelikleri düşürür."""
    subs = list((await db.execute(select(Subscription))).scalars().all())
    gateway = get_gateway()
    synced = downgraded = 0
    now = utcnow()

    for sub in subs:
        if sub.provider_subscription_id:
            try:
                remote = gateway.fetch_subscription(sub.provider_subscription_id)
            except Exception:  # sağlayıcı erişilemezse diğer abonelikler etkilenmesin
                remote = None
            if remote and remote.get("status"):
                raw = str(remote["status"])
                if raw in set(SubscriptionStatus):
                    sub.status = SubscriptionStatus(raw)
                    synced += 1
                period_end = _to_datetime(remote.get("current_period_end"))
                if period_end:
                    sub.current_period_end = period_end

        period_end = ensure_utc(sub.current_period_end) if sub.current_period_end else None
        expired = period_end is not None and period_end < now
        if sub.plan != Plan.FREE and (
            sub.status == SubscriptionStatus.CANCELED
            or (expired and sub.cancel_at_period_end)
        ):
            sub.plan = Plan.FREE
            sub.status = SubscriptionStatus.CANCELED
            downgraded += 1
        await _sync_org_plan(db, sub)

    await db.commit()
    return {"synced": synced, "downgraded": downgraded}


async def usage_summary(db: AsyncSession, org_id: uuid.UUID) -> dict[str, Any]:
    sub = await get_subscription(db, org_id)
    spec = plan_catalog()[sub.plan]
    return {
        "plan": sub.plan,
        "status": sub.status,
        "cancel_at_period_end": sub.cancel_at_period_end,
        "current_period_end": sub.current_period_end,
        "documents_used": await usage.document_count(db, org_id),
        "documents_limit": spec.documents,
        "storage_bytes_used": await usage.storage_bytes(db, org_id),
        "storage_bytes_limit": quota.storage_limit_bytes(sub.plan),
        "ai_requests_used": await usage.current(db, org_id, UsageMetric.AI_REQUESTS),
        "ai_requests_limit": spec.ai_requests,
        "ai_tokens_used": await usage.current(db, org_id, UsageMetric.AI_TOKENS),
        "ai_tokens_limit": spec.ai_tokens,
    }
