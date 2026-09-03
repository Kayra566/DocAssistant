import pytest

from app.core import crypto
from app.core.config import settings
from app.core.logging import mask_pii
from tests.conftest import STRONG_PASSWORD, auth_headers, register_user, setup_org


def test_encrypt_roundtrip_hides_plaintext():
    secret = "JBSWY3DPEHPK3PXP"
    encrypted = crypto.encrypt(secret)

    assert encrypted != secret
    assert secret not in encrypted
    assert crypto.decrypt(encrypted) == secret


def test_decrypt_passes_through_legacy_plaintext():
    assert crypto.decrypt("legacy-secret") == "legacy-secret"


def test_encrypt_uses_fresh_nonce_each_time():
    assert crypto.encrypt("same") != crypto.encrypt("same")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("user ali@example.com giris yapti", "user <email> giris yapti"),
        ("Authorization: Bearer abc.def.ghi", "Authorization: <redacted>"),
        ('{"password": "Sup3rSecret!"}', '{"password": "<redacted>"}'),
        ("kart 4242 4242 4242 4242 kullanildi", "kart <card> kullanildi"),
    ],
)
def test_mask_pii_redacts_sensitive_values(raw, expected):
    assert mask_pii(raw) == expected


async def test_security_headers_present(client):
    resp = await client.get("/api/v1/health")

    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "no-referrer"
    assert "default-src 'self'" in resp.headers["Content-Security-Policy"]


async def test_auth_endpoints_are_rate_limited(client):
    limit = settings.RATE_LIMIT_AUTH_REQUESTS
    last = None
    for index in range(limit + 2):
        last = await client.post(
            "/api/v1/auth/login",
            json={"email": f"rl-{index}@example.com", "password": STRONG_PASSWORD},
        )

    assert last.status_code == 429
    assert last.headers["Retry-After"].isdigit()
    assert "Çok fazla istek" in last.json()["detail"]


async def test_health_endpoint_is_exempt_from_rate_limit(client):
    for _ in range(settings.RATE_LIMIT_AUTH_REQUESTS + 5):
        resp = await client.get("/health")
    assert resp.status_code == 200


async def test_totp_secret_is_encrypted_at_rest(client):
    from sqlalchemy import select, text

    from app.models.user import User
    from tests.conftest import TestSessionLocal

    email = "totp@example.com"
    await register_user(client, email)

    async with TestSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one()
        user.totp_secret = "JBSWY3DPEHPK3PXP"
        await db.commit()

        # TypeDecorator'ı atlayarak diskteki ham değeri okur.
        raw = (
            await db.execute(
                text("SELECT totp_secret FROM users WHERE email = :email"),
                {"email": email},
            )
        ).scalar_one()

    assert raw.startswith("enc:v1:")
    assert "JBSWY3DPEHPK3PXP" not in raw

    async with TestSessionLocal() as db:
        reloaded = (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one()
    assert reloaded.totp_secret == "JBSWY3DPEHPK3PXP"


async def test_error_messages_are_localized_by_accept_language(client):
    resp = await client.get(
        "/api/v1/organizations", headers={"Accept-Language": "en-US,en;q=0.9"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Authorization header is missing."

    tr = await client.get("/api/v1/organizations", headers={"Accept-Language": "tr"})
    assert tr.json()["detail"] == "Yetkilendirme başlığı eksik."


async def test_features_endpoint_reports_flags(client):
    resp = await client.get("/api/v1/features")
    assert resp.status_code == 200
    body = resp.json()
    assert "onboarding" in body["flags"]
    assert body["sentry_enabled"] is False


async def test_metrics_endpoint_exposes_prometheus_format(client):
    await client.get("/api/v1/health")
    resp = await client.get("/metrics")

    assert resp.status_code == 200
    assert "http_requests_total" in resp.text


async def test_audit_chain_valid_and_detects_tampering(client):
    from sqlalchemy import select

    from app.core import audit
    from app.models.collab import ActivityLog
    from tests.conftest import TestSessionLocal

    access, org_id = await setup_org(client, "audit@example.com")
    await client.post(
        f"/api/v1/documents/{org_id}/upload",
        headers=auth_headers(access),
        files={"file": ("a.txt", b"denetim kaydi icerigi", "text/plain")},
    )

    async with TestSessionLocal() as db:
        import uuid

        result = await audit.verify_chain(db, uuid.UUID(org_id))
        assert result["valid"] is True
        assert result["checked"] >= 1

        entry = (
            await db.execute(select(ActivityLog).limit(1))
        ).scalar_one()
        entry.action = "document.tampered"
        await db.commit()

        broken = await audit.verify_chain(db, uuid.UUID(org_id))

    assert broken["valid"] is False
    assert broken["broken_at"] is not None
