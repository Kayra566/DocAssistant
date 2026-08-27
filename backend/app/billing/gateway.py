from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from typing import Any, Protocol

from app.billing.plans import price_id
from app.core.config import settings
from app.core.exceptions import AuthError, ValidationError
from app.models.enums import Plan


class BillingGateway(Protocol):
    def create_checkout_session(
        self, *, org_id: uuid.UUID, plan: Plan, customer_id: str | None, email: str
    ) -> dict[str, Any]: ...

    def create_portal_session(self, *, customer_id: str) -> dict[str, Any]: ...

    def parse_event(self, payload: bytes, signature: str | None) -> dict[str, Any]: ...

    def fetch_subscription(self, subscription_id: str) -> dict[str, Any]: ...


class FakeGateway:
    """Stripe olmadan checkout/portal/webhook akışını taklit eder (dev/test)."""

    def create_checkout_session(
        self, *, org_id: uuid.UUID, plan: Plan, customer_id: str | None, email: str
    ) -> dict[str, Any]:
        session_id = f"cs_fake_{uuid.uuid4().hex[:16]}"
        return {
            "id": session_id,
            "url": f"{settings.BILLING_SUCCESS_URL}&session_id={session_id}",
            "customer": customer_id or f"cus_fake_{org_id.hex[:12]}",
        }

    def create_portal_session(self, *, customer_id: str) -> dict[str, Any]:
        return {
            "id": f"bps_fake_{uuid.uuid4().hex[:12]}",
            "url": f"{settings.BILLING_PORTAL_RETURN_URL}?customer={customer_id}",
        }

    def parse_event(self, payload: bytes, signature: str | None) -> dict[str, Any]:
        """Fake modda imza opsiyoneldir; ayarlıysa HMAC-SHA256 beklenir."""
        secret = settings.STRIPE_WEBHOOK_SECRET
        if secret:
            expected = hmac.new(
                secret.encode("utf-8"), payload, hashlib.sha256
            ).hexdigest()
            if not signature or not hmac.compare_digest(expected, signature):
                raise AuthError("Webhook imzası geçersiz.")
        try:
            event = json.loads(payload)
        except ValueError as exc:
            raise ValidationError("Webhook gövdesi geçersiz JSON.") from exc
        if not isinstance(event, dict) or "id" not in event or "type" not in event:
            raise ValidationError("Webhook event'i 'id' ve 'type' içermeli.")
        return event

    def fetch_subscription(self, subscription_id: str) -> dict[str, Any]:
        return {"id": subscription_id, "status": "active"}


class StripeGateway:
    def __init__(self) -> None:
        import stripe

        if not settings.STRIPE_SECRET_KEY:
            raise ValidationError("STRIPE_SECRET_KEY tanımlı değil.")
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self._stripe = stripe

    def create_checkout_session(
        self, *, org_id: uuid.UUID, plan: Plan, customer_id: str | None, email: str
    ) -> dict[str, Any]:
        session = self._stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id or None,
            customer_email=None if customer_id else email,
            line_items=[{"price": price_id(plan), "quantity": 1}],
            success_url=settings.BILLING_SUCCESS_URL,
            cancel_url=settings.BILLING_CANCEL_URL,
            client_reference_id=str(org_id),
            metadata={"organization_id": str(org_id), "plan": plan},
            subscription_data={"metadata": {"organization_id": str(org_id)}},
        )
        return dict(session)

    def create_portal_session(self, *, customer_id: str) -> dict[str, Any]:
        session = self._stripe.billing_portal.Session.create(
            customer=customer_id, return_url=settings.BILLING_PORTAL_RETURN_URL
        )
        return dict(session)

    def parse_event(self, payload: bytes, signature: str | None) -> dict[str, Any]:
        if not signature:
            raise AuthError("Stripe-Signature başlığı eksik.")
        try:
            event = self._stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
        except Exception as exc:
            raise AuthError("Webhook imzası doğrulanamadı.") from exc
        return dict(event)

    def fetch_subscription(self, subscription_id: str) -> dict[str, Any]:
        return dict(self._stripe.Subscription.retrieve(subscription_id))


_gateway: BillingGateway | None = None


def get_gateway() -> BillingGateway:
    global _gateway
    if _gateway is None:
        _gateway = (
            StripeGateway() if settings.BILLING_PROVIDER == "stripe" else FakeGateway()
        )
    return _gateway
