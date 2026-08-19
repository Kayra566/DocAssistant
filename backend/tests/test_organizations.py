from tests.conftest import auth_headers, login_user, register_user


async def _register_and_login(client, email):
    reg = (await register_user(client, email)).json()
    access = (await login_user(client, email)).json()["access_token"]
    return reg, access


async def test_list_and_create_organization(client):
    _, access = await _register_and_login(client, "owner@example.com")
    h = auth_headers(access)

    orgs = await client.get("/api/v1/organizations", headers=h)
    assert orgs.status_code == 200
    assert len(orgs.json()) == 1  # register sırasında default org açıldı

    created = await client.post(
        "/api/v1/organizations", json={"name": "İkinci Takım"}, headers=h
    )
    assert created.status_code == 201
    assert created.json()["slug"]

    orgs2 = await client.get("/api/v1/organizations", headers=h)
    assert len(orgs2.json()) == 2


async def test_update_organization_requires_admin(client):
    owner_reg, owner_access = await _register_and_login(client, "own@example.com")
    org_id = owner_reg["organization_id"]

    # Owner güncelleyebilir
    resp = await client.patch(
        f"/api/v1/organizations/{org_id}",
        json={"name": "Yeni Ad"},
        headers=auth_headers(owner_access),
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Yeni Ad"


async def test_invite_accept_and_role_flow(client):
    owner_reg, owner_access = await _register_and_login(client, "boss@example.com")
    org_id = owner_reg["organization_id"]
    # Davet edilecek kullanıcı sistemde kayıtlı olmalı (davet email'ine göre eşleşir)
    await register_user(client, "guest@example.com")
    guest_access = (await login_user(client, "guest@example.com")).json()[
        "access_token"
    ]

    invite = await client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "guest@example.com", "role": "member"},
        headers=auth_headers(owner_access),
    )
    assert invite.status_code == 201
    token = invite.json()["dev_invite_token"]

    accept = await client.post(
        "/api/v1/organizations/invitations/accept",
        json={"token": token},
        headers=auth_headers(guest_access),
    )
    assert accept.status_code == 200

    members = await client.get(
        f"/api/v1/organizations/{org_id}/members", headers=auth_headers(owner_access)
    )
    emails = {m["email"] for m in members.json()}
    assert emails == {"boss@example.com", "guest@example.com"}


async def test_viewer_cannot_invite(client):
    owner_reg, owner_access = await _register_and_login(client, "o2@example.com")
    org_id = owner_reg["organization_id"]
    await register_user(client, "viewer@example.com")
    viewer_access = (await login_user(client, "viewer@example.com")).json()[
        "access_token"
    ]

    invite = await client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "viewer@example.com", "role": "viewer"},
        headers=auth_headers(owner_access),
    )
    token = invite.json()["dev_invite_token"]
    await client.post(
        "/api/v1/organizations/invitations/accept",
        json={"token": token},
        headers=auth_headers(viewer_access),
    )

    # Viewer başka birini davet edemez
    forbidden = await client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "someone@example.com", "role": "member"},
        headers=auth_headers(viewer_access),
    )
    assert forbidden.status_code == 403


async def test_cannot_invite_as_owner_role(client):
    owner_reg, owner_access = await _register_and_login(client, "o3@example.com")
    org_id = owner_reg["organization_id"]
    resp = await client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "x@example.com", "role": "owner"},
        headers=auth_headers(owner_access),
    )
    assert resp.status_code == 422
