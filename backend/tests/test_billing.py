import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.config import settings
from tests.conftest import STRONG_PASSWORD, auth_headers, login_user, register_user, setup_org


def webhook_body(event: dict) -> tuple[bytes, dict[str, str]]:
    payload = json.dumps(event).encode("utf-8")
    headers = {}
    if settings.STRIPE_WEBHOOK_SECRET:
        headers["Stripe-Signature"] = hmac.new(
            settings.STRIPE_WEBHOOK_SECRET.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()
    return payload, headers


async def send_webhook(client, event: dict):
    payload, headers = webhook_body(event)
    return await client.post(
        "/api/v1/billing/webhook",
        content=payload,
        headers={"content-type": "application/json", **headers},
    )


async def org_plan(client, access: str, org_id: str) -> str:
    orgs = (await client.get("/api/v1/organizations", headers=auth_headers(access))).json()
    return next(o["plan"] for o in orgs if o["id"] == org_id)


def subscription_event(org_id: str, *, event_id: str, plan: str, **overrides) -> dict:
    obj = {
        "id": f"sub_{org_id[:8]}",
        "customer": f"cus_{org_id[:8]}",
        "status": "active",
        "cancel_at_period_end": False,
        "current_period_end": int(
            (datetime.now(UTC) + timedelta(days=30)).timestamp()
        ),
        "metadata": {"organization_id": org_id, "plan": plan},
    }
    obj.update(overrides)
    return {
        "id": event_id,
        "type": "customer.subscription.updated",
        "data": {"object": obj},
    }


async def test_plans_endpoint_lists_three_tiers(client):
    resp = await client.get("/api/v1/billing/plans")
    assert resp.status_code == 200
    plans = {p["key"]: p for p in resp.json()}
    assert set(plans) == {"free", "pro", "business"}
    assert plans["free"]["price_monthly"] == 0
    assert plans["pro"]["price_monthly"] > 0
    assert plans["free"]["documents"] < plans["pro"]["documents"]


async def test_new_org_starts_on_free_plan(client):
    access, org_id = await setup_org(client, "bill-free@example.com")
    resp = await client.get(
        f"/api/v1/billing/{org_id}/subscription", headers=auth_headers(access)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan"] == "free"
    assert body["status"] == "active"


async def test_checkout_returns_session_url(client):
    access, org_id = await setup_org(client, "bill-checkout@example.com")
    resp = await client.post(
        f"/api/v1/billing/{org_id}/checkout",
        headers=auth_headers(access),
        json={"plan": "pro"},
    )
    assert resp.status_code == 200
    assert resp.json()["url"].startswith("http")
    assert resp.json()["session_id"]


async def test_checkout_rejects_free_plan(client):
    access, org_id = await setup_org(client, "bill-free-checkout@example.com")
    resp = await client.post(
        f"/api/v1/billing/{org_id}/checkout",
        headers=auth_headers(access),
        json={"plan": "free"},
    )
    assert resp.status_code == 422


async def test_checkout_requires_owner_role(client):
    owner_access, org_id = await setup_org(client, "bill-owner@example.com")
    await register_user(client, "bill-member@example.com")
    invite = await client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers=auth_headers(owner_access),
        json={"email": "bill-member@example.com", "role": "member"},
    )
    member_access = (
        await login_user(client, "bill-member@example.com", STRONG_PASSWORD)
    ).json()["access_token"]
    await client.post(
        "/api/v1/organizations/invitations/accept",
        headers=auth_headers(member_access),
        json={"token": invite.json()["dev_invite_token"]},
    )

    resp = await client.post(
        f"/api/v1/billing/{org_id}/checkout",
        headers=auth_headers(member_access),
        json={"plan": "pro"},
    )
    assert resp.status_code == 403


async def test_webhook_upgrades_plan(client):
    access, org_id = await setup_org(client, "bill-upgrade@example.com")
    resp = await send_webhook(
        client, subscription_event(org_id, event_id="evt_1", plan="pro")
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "applied"

    sub = (
        await client.get(
            f"/api/v1/billing/{org_id}/subscription", headers=auth_headers(access)
        )
    ).json()
    assert sub["plan"] == "pro"
    assert sub["status"] == "active"

    assert await org_plan(client, access, org_id) == "pro"


async def test_webhook_is_idempotent(client):
    access, org_id = await setup_org(client, "bill-idem@example.com")
    event = subscription_event(org_id, event_id="evt_dup", plan="pro")
    first = await send_webhook(client, event)
    second = await send_webhook(client, event)
    assert first.json()["status"] == "applied"
    assert second.json()["status"] == "duplicate"


async def test_webhook_cancellation_drops_to_free(client):
    access, org_id = await setup_org(client, "bill-cancel@example.com")
    await send_webhook(client, subscription_event(org_id, event_id="evt_up", plan="pro"))

    cancel = subscription_event(org_id, event_id="evt_del", plan="pro")
    cancel["type"] = "customer.subscription.deleted"
    resp = await send_webhook(client, cancel)
    assert resp.json()["status"] == "applied"

    sub = (
        await client.get(
            f"/api/v1/billing/{org_id}/subscription", headers=auth_headers(access)
        )
    ).json()
    assert sub["plan"] == "free"
    assert sub["status"] == "canceled"


async def test_webhook_payment_failure_marks_past_due(client):
    access, org_id = await setup_org(client, "bill-pastdue@example.com")
    await send_webhook(client, subscription_event(org_id, event_id="evt_ok", plan="pro"))

    failure = {
        "id": "evt_fail",
        "type": "invoice.payment_failed",
        "data": {"object": {"metadata": {"organization_id": org_id}}},
    }
    await send_webhook(client, failure)

    sub = (
        await client.get(
            f"/api/v1/billing/{org_id}/subscription", headers=auth_headers(access)
        )
    ).json()
    assert sub["status"] == "past_due"
    # Ödeme başarısızsa organizasyon Free kotalarına düşer.
    assert await org_plan(client, access, org_id) == "free"


async def test_webhook_rejects_invalid_json(client):
    resp = await client.post(
        "/api/v1/billing/webhook",
        content=b"not-json",
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 422


async def test_document_quota_blocks_after_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "QUOTA_FREE_DOCUMENTS", 2)
    access, org_id = await setup_org(client, "bill-docquota@example.com")

    for i in range(2):
        ok = await client.post(
            f"/api/v1/documents/{org_id}/upload",
            headers=auth_headers(access),
            files={"file": (f"a{i}.txt", b"merhaba dunya", "text/plain")},
        )
        assert ok.status_code == 201, ok.text

    blocked = await client.post(
        f"/api/v1/documents/{org_id}/upload",
        headers=auth_headers(access),
        files={"file": ("c.txt", b"merhaba dunya", "text/plain")},
    )
    assert blocked.status_code == 402


async def test_storage_quota_blocks_large_upload(client, monkeypatch):
    monkeypatch.setattr(settings, "QUOTA_FREE_STORAGE_MB", 0)
    access, org_id = await setup_org(client, "bill-storage@example.com")
    resp = await client.post(
        f"/api/v1/documents/{org_id}/upload",
        headers=auth_headers(access),
        files={"file": ("a.txt", b"merhaba dunya", "text/plain")},
    )
    assert resp.status_code == 402


async def test_ai_request_quota_blocks_after_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "QUOTA_FREE_AI_REQUESTS", 1)
    access, org_id = await setup_org(client, "bill-aiquota@example.com")
    doc = (
        await client.post(
            f"/api/v1/documents/{org_id}/upload",
            headers=auth_headers(access),
            files={"file": ("a.txt", b"Toplam bedel 100 TL olarak belirlendi.", "text/plain")},
        )
    ).json()

    first = await client.post(
        f"/api/v1/ai/{org_id}/chat",
        headers=auth_headers(access),
        json={"document_id": doc["id"], "question": "Bedel nedir?"},
    )
    assert first.status_code == 200

    second = await client.post(
        f"/api/v1/ai/{org_id}/chat",
        headers=auth_headers(access),
        json={"document_id": doc["id"], "question": "Başka ne var?"},
    )
    assert second.status_code == 402


async def test_usage_endpoint_reports_all_metrics(client):
    access, org_id = await setup_org(client, "bill-usage@example.com")
    doc = (
        await client.post(
            f"/api/v1/documents/{org_id}/upload",
            headers=auth_headers(access),
            files={"file": ("a.txt", b"Sozlesme bedeli 500 TL olarak belirlendi.", "text/plain")},
        )
    ).json()
    await client.post(
        f"/api/v1/ai/{org_id}/summary",
        headers=auth_headers(access),
        json={"document_id": doc["id"]},
    )

    resp = await client.get(
        f"/api/v1/billing/{org_id}/usage", headers=auth_headers(access)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan"] == "free"
    assert body["documents_used"] == 1
    assert body["storage_bytes_used"] > 0
    assert body["ai_requests_used"] == 1
    assert body["ai_tokens_used"] > 0
    assert body["ai_requests_limit"] > 0


async def test_portal_requires_customer(client):
    access, org_id = await setup_org(client, "bill-portal@example.com")
    missing = await client.post(
        f"/api/v1/billing/{org_id}/portal", headers=auth_headers(access)
    )
    assert missing.status_code == 422

    await client.post(
        f"/api/v1/billing/{org_id}/checkout",
        headers=auth_headers(access),
        json={"plan": "pro"},
    )
    resp = await client.post(
        f"/api/v1/billing/{org_id}/portal", headers=auth_headers(access)
    )
    assert resp.status_code == 200
    assert resp.json()["url"].startswith("http")


async def test_billing_is_tenant_isolated(client):
    _, org_a = await setup_org(client, "bill-iso-a@example.com")
    access_b, _ = await setup_org(client, "bill-iso-b@example.com")
    resp = await client.get(
        f"/api/v1/billing/{org_a}/subscription", headers=auth_headers(access_b)
    )
    assert resp.status_code == 403


@pytest.mark.parametrize("cancel_at_period_end", [True, False])
async def test_reconcile_downgrades_expired_subscription(client, cancel_at_period_end):
    from app.services.billing import get_subscription, reconcile
    from tests.conftest import TestSessionLocal

    _, org_id = await setup_org(client, f"bill-rec-{cancel_at_period_end}@example.com")
    await send_webhook(
        client,
        subscription_event(
            org_id,
            event_id=f"evt_rec_{cancel_at_period_end}",
            plan="pro",
            cancel_at_period_end=cancel_at_period_end,
            current_period_end=int(
                (datetime.now(UTC) - timedelta(days=1)).timestamp()
            ),
        ),
    )

    async with TestSessionLocal() as db:
        result = await reconcile(db)
        sub = await get_subscription(db, uuid.UUID(org_id))
        assert sub.plan == ("free" if cancel_at_period_end else "pro")
        assert result["downgraded"] == (1 if cancel_at_period_end else 0)
