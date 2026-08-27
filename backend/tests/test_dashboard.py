from datetime import UTC, datetime

from sqlalchemy import select

from app.models.user import User
from tests.conftest import TestSessionLocal, auth_headers, setup_org

DOC_TEXT = "Bütçe raporu 2025 yılı için hazırlandı. Toplam tutar 120000 TL'dir."


async def _setup(client, email):
    access, org_id = await setup_org(client, email)
    doc = (
        await client.post(
            f"/api/v1/documents/{org_id}/upload",
            headers=auth_headers(access),
            files={"file": ("butce.txt", DOC_TEXT.encode("utf-8"), "text/plain")},
        )
    ).json()
    return access, org_id, doc


async def _make_superuser(email: str) -> None:
    async with TestSessionLocal() as db:
        user = (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one()
        user.is_superuser = True
        await db.commit()


async def test_dashboard_stats_include_totals_and_quota(client):
    access, org_id, doc = await _setup(client, "dash-a@example.com")
    await client.post(
        f"/api/v1/ai/{org_id}/summary",
        headers=auth_headers(access),
        json={"document_id": doc["id"], "level": "short"},
    )

    resp = await client.get(
        f"/api/v1/dashboard/{org_id}/stats", headers=auth_headers(access)
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["plan"] == "free"
    assert body["totals"]["documents"] == 1
    assert body["totals"]["ai_jobs"] == 1
    assert body["totals"]["members"] == 1
    assert body["quota"]["documents_limit"] > 0
    assert body["quota"]["ai_requests_used"] >= 1


async def test_dashboard_trend_covers_configured_window(client):
    access, org_id, _ = await _setup(client, "dash-b@example.com")

    body = (
        await client.get(
            f"/api/v1/dashboard/{org_id}/stats", headers=auth_headers(access)
        )
    ).json()
    trend = body["usage_trend"]

    assert len(trend) == 30
    assert trend[-1]["date"] == datetime.now(UTC).date().isoformat()
    assert trend[-1]["documents"] == 1
    assert sum(point["documents"] for point in trend) == 1


async def test_job_distribution_groups_by_type(client):
    access, org_id, doc = await _setup(client, "dash-c@example.com")
    for level in ("short", "detailed"):
        await client.post(
            f"/api/v1/ai/{org_id}/summary",
            headers=auth_headers(access),
            json={"document_id": doc["id"], "level": level},
        )
    await client.post(
        f"/api/v1/ai/{org_id}/keypoints",
        headers=auth_headers(access),
        json={"document_id": doc["id"]},
    )

    body = (
        await client.get(
            f"/api/v1/dashboard/{org_id}/stats", headers=auth_headers(access)
        )
    ).json()
    distribution = {row["key"]: row["count"] for row in body["job_distribution"]}
    assert distribution["summary"] == 2
    assert distribution["keypoints"] == 1
    assert body["document_status"] == [{"key": "ready", "count": 1}]


async def test_stats_require_membership(client):
    _, org_id, _ = await _setup(client, "dash-owner@example.com")
    outsider, _ = await setup_org(client, "dash-outsider@example.com")

    resp = await client.get(
        f"/api/v1/dashboard/{org_id}/stats", headers=auth_headers(outsider)
    )
    assert resp.status_code == 403


async def test_admin_endpoints_require_superuser(client):
    access, _, _ = await _setup(client, "plain-user@example.com")
    assert (
        await client.get("/api/v1/admin/stats", headers=auth_headers(access))
    ).status_code == 403


async def test_superuser_sees_platform_stats(client):
    email = "root@example.com"
    access, _, _ = await _setup(client, email)
    await _make_superuser(email)

    stats = await client.get("/api/v1/admin/stats", headers=auth_headers(access))
    assert stats.status_code == 200, stats.text
    body = stats.json()
    assert body["users"] >= 1
    assert body["organizations"] >= 1
    assert body["documents"] >= 1
    assert body["plan_distribution"][0]["key"] == "free"

    orgs = await client.get(
        "/api/v1/admin/organizations", headers=auth_headers(access)
    )
    assert orgs.status_code == 200
    assert orgs.json()[0]["documents"] == 1
    assert orgs.json()[0]["members"] == 1
