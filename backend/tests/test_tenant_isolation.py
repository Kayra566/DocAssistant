import uuid

from tests.conftest import auth_headers, login_user, register_user


async def test_tenant_isolation_members(client):
    """Bir kullanıcı, üyesi olmadığı organizasyonun üyelerini göremez."""
    a_reg = (await register_user(client, "tenant-a@example.com")).json()
    a_access = (await login_user(client, "tenant-a@example.com")).json()[
        "access_token"
    ]
    b_reg = (await register_user(client, "tenant-b@example.com")).json()

    a_org = a_reg["organization_id"]
    b_org = b_reg["organization_id"]
    assert a_org != b_org

    # A, kendi org üyelerini görebilir
    ok = await client.get(
        f"/api/v1/organizations/{a_org}/members", headers=auth_headers(a_access)
    )
    assert ok.status_code == 200

    # A, B'nin org'una erişemez (üye değil → 403)
    forbidden = await client.get(
        f"/api/v1/organizations/{b_org}/members", headers=auth_headers(a_access)
    )
    assert forbidden.status_code == 403


async def test_cannot_update_foreign_org(client):
    await register_user(client, "x-a@example.com")
    a_access = (await login_user(client, "x-a@example.com")).json()["access_token"]
    b_reg = (await register_user(client, "x-b@example.com")).json()

    resp = await client.patch(
        f"/api/v1/organizations/{b_reg['organization_id']}",
        json={"name": "Ele geçirildi"},
        headers=auth_headers(a_access),
    )
    assert resp.status_code == 403


async def test_nonexistent_org_returns_403(client):
    await register_user(client, "solo@example.com")
    access = (await login_user(client, "solo@example.com")).json()["access_token"]
    resp = await client.get(
        f"/api/v1/organizations/{uuid.uuid4()}/members",
        headers=auth_headers(access),
    )
    assert resp.status_code == 403
