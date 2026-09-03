import json

from tests.conftest import STRONG_PASSWORD, auth_headers, login_user, setup_org

DOC = b"GDPR testi icin ornek dokuman icerigi."


async def _setup(client, email):
    access, org_id = await setup_org(client, email)
    doc = (
        await client.post(
            f"/api/v1/documents/{org_id}/upload",
            headers=auth_headers(access),
            files={"file": ("veri.txt", DOC, "text/plain")},
        )
    ).json()
    return access, org_id, doc


async def test_export_returns_full_dataset_as_download(client):
    access, org_id, doc = await _setup(client, "gdpr-export@example.com")
    await client.post(
        f"/api/v1/ai/{org_id}/summary",
        headers=auth_headers(access),
        json={"document_id": doc["id"], "level": "short"},
    )

    resp = await client.get("/api/v1/gdpr/export", headers=auth_headers(access))
    assert resp.status_code == 200
    assert "attachment" in resp.headers["content-disposition"]

    payload = json.loads(resp.content)
    assert payload["user"]["email"] == "gdpr-export@example.com"
    assert len(payload["documents"]) == 1
    assert len(payload["ai_jobs"]) == 1
    assert payload["organizations"][0]["id"] == org_id
    # Parola özeti hiçbir koşulda dışa aktarılmaz.
    assert "hashed_password" not in payload["user"]


async def test_export_requires_authentication(client):
    assert (await client.get("/api/v1/gdpr/export")).status_code == 401


async def test_delete_account_requires_password_and_confirmation(client):
    access, _, _ = await _setup(client, "gdpr-guard@example.com")

    unconfirmed = await client.post(
        "/api/v1/gdpr/delete-account",
        headers=auth_headers(access),
        json={"password": STRONG_PASSWORD, "confirm": False},
    )
    assert unconfirmed.status_code == 422

    wrong_password = await client.post(
        "/api/v1/gdpr/delete-account",
        headers=auth_headers(access),
        json={"password": "yanlis-parola", "confirm": True},
    )
    assert wrong_password.status_code == 401


async def test_delete_account_removes_user_and_sole_owned_org(client):
    access, org_id, _ = await _setup(client, "gdpr-delete@example.com")

    resp = await client.post(
        "/api/v1/gdpr/delete-account",
        headers=auth_headers(access),
        json={"password": STRONG_PASSWORD, "confirm": True},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["organizations_deleted"] == 1
    assert resp.json()["files_deleted"] == 1

    assert (await login_user(client, "gdpr-delete@example.com")).status_code == 401
    assert (
        await client.get(f"/api/v1/documents/{org_id}", headers=auth_headers(access))
    ).status_code == 401


async def test_delete_account_keeps_org_with_another_owner(client):
    owner_access, org_id, _ = await _setup(client, "gdpr-owner@example.com")
    second_access, _ = await setup_org(client, "gdpr-second@example.com")

    invite = await client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers=auth_headers(owner_access),
        json={"email": "gdpr-second@example.com", "role": "admin"},
    )
    await client.post(
        "/api/v1/organizations/invitations/accept",
        headers=auth_headers(second_access),
        json={"token": invite.json()["dev_invite_token"]},
    )
    second_id = (
        await client.get("/api/v1/auth/me", headers=auth_headers(second_access))
    ).json()["id"]
    promoted = await client.patch(
        f"/api/v1/organizations/{org_id}/members/{second_id}",
        headers=auth_headers(owner_access),
        json={"role": "owner"},
    )
    assert promoted.status_code == 200, promoted.text

    resp = await client.post(
        "/api/v1/gdpr/delete-account",
        headers=auth_headers(owner_access),
        json={"password": STRONG_PASSWORD, "confirm": True},
    )
    assert resp.status_code == 200
    assert resp.json()["organizations_deleted"] == 0

    still_there = await client.get(
        f"/api/v1/documents/{org_id}", headers=auth_headers(second_access)
    )
    assert still_there.status_code == 200
