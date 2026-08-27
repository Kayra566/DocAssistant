from tests.conftest import auth_headers, register_user, setup_org

DOC_TEXT = (
    "Rapor 12.02.2025 tarihinde yayımlandı. Toplam bütçe 480000 TL olarak "
    "onaylandı. Proje yöneticisi Ayşe Yılmaz'dır. Teslim süresi 60 gündür."
)


async def _upload(client, access, org_id, filename="rapor.txt"):
    resp = await client.post(
        f"/api/v1/documents/{org_id}/upload",
        headers=auth_headers(access),
        files={"file": (filename, DOC_TEXT.encode("utf-8"), "text/plain")},
    )
    return resp.json()


async def _setup(client, email):
    access, org_id = await setup_org(client, email)
    return access, org_id, await _upload(client, access, org_id)


async def _create_share(client, access, org_id, doc_id, **payload):
    return await client.post(
        f"/api/v1/shares/{org_id}",
        headers=auth_headers(access),
        json={"document_id": doc_id, **payload},
    )


async def test_create_share_link_returns_token_once(client):
    access, org_id, doc = await _setup(client, "share-a@example.com")
    resp = await _create_share(client, access, org_id, doc["id"])
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["token"]
    assert body["url"].endswith(body["token"])
    assert body["permission"] == "view"

    listed = await client.get(
        f"/api/v1/shares/{org_id}", headers=auth_headers(access)
    )
    assert listed.status_code == 200
    assert "token" not in listed.json()[0]


async def test_public_share_grants_access_and_counts_views(client):
    access, org_id, doc = await _setup(client, "share-b@example.com")
    token = (await _create_share(client, access, org_id, doc["id"])).json()["token"]

    resp = await client.get(f"/api/v1/shares/public/{token}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["filename"] == doc["filename"]
    assert body["can_download"] is False

    listed = (
        await client.get(f"/api/v1/shares/{org_id}", headers=auth_headers(access))
    ).json()
    assert listed[0]["view_count"] == 1


async def test_view_permission_blocks_download(client):
    access, org_id, doc = await _setup(client, "share-c@example.com")
    token = (await _create_share(client, access, org_id, doc["id"])).json()["token"]

    resp = await client.get(f"/api/v1/shares/public/{token}/download")
    assert resp.status_code == 403


async def test_download_permission_returns_file(client):
    access, org_id, doc = await _setup(client, "share-d@example.com")
    token = (
        await _create_share(client, access, org_id, doc["id"], permission="download")
    ).json()["token"]

    resp = await client.get(f"/api/v1/shares/public/{token}/download")
    assert resp.status_code == 200
    assert DOC_TEXT.encode("utf-8") in resp.content


async def test_email_specific_share_requires_matching_email(client):
    access, org_id, doc = await _setup(client, "share-e@example.com")
    token = (
        await _create_share(
            client, access, org_id, doc["id"], email="guest@example.com"
        )
    ).json()["token"]

    assert (await client.get(f"/api/v1/shares/public/{token}")).status_code == 401
    ok = await client.get(
        f"/api/v1/shares/public/{token}", params={"email": "GUEST@example.com"}
    )
    assert ok.status_code == 200


async def test_revoked_share_is_rejected(client):
    access, org_id, doc = await _setup(client, "share-f@example.com")
    created = (await _create_share(client, access, org_id, doc["id"])).json()

    revoked = await client.delete(
        f"/api/v1/shares/{org_id}/{created['id']}", headers=auth_headers(access)
    )
    assert revoked.status_code == 200
    assert revoked.json()["revoked"] is True

    assert (
        await client.get(f"/api/v1/shares/public/{created['token']}")
    ).status_code == 401


async def test_invalid_token_is_rejected(client):
    resp = await client.get("/api/v1/shares/public/not-a-real-token")
    assert resp.status_code == 401


async def test_other_org_cannot_list_shares(client):
    access, org_id, doc = await _setup(client, "share-owner@example.com")
    await _create_share(client, access, org_id, doc["id"])

    outsider, _ = await setup_org(client, "share-outsider@example.com")
    resp = await client.get(
        f"/api/v1/shares/{org_id}", headers=auth_headers(outsider)
    )
    assert resp.status_code == 403


async def test_comments_crud_and_author_permissions(client):
    access, org_id, doc = await _setup(client, "comment-owner@example.com")

    created = await client.post(
        f"/api/v1/documents/{org_id}/{doc['id']}/comments",
        headers=auth_headers(access),
        json={"content": "İkinci sayfadaki tutar kontrol edilmeli.", "page": 2},
    )
    assert created.status_code == 201, created.text
    assert created.json()["author_email"] == "comment-owner@example.com"

    listed = await client.get(
        f"/api/v1/documents/{org_id}/{doc['id']}/comments",
        headers=auth_headers(access),
    )
    assert len(listed.json()) == 1

    deleted = await client.delete(
        f"/api/v1/documents/{org_id}/{doc['id']}/comments/{created.json()['id']}",
        headers=auth_headers(access),
    )
    assert deleted.status_code == 204


async def test_activity_log_records_document_and_share_actions(client):
    access, org_id, doc = await _setup(client, "activity@example.com")
    await _create_share(client, access, org_id, doc["id"])

    resp = await client.get(
        f"/api/v1/dashboard/{org_id}/activity", headers=auth_headers(access)
    )
    assert resp.status_code == 200, resp.text
    actions = {row["action"] for row in resp.json()}
    assert {"document.uploaded", "share.created"} <= actions
    assert all(row["actor_email"] == "activity@example.com" for row in resp.json())


async def test_register_user_helper_creates_isolated_orgs(client):
    """Paylaşım testleri için kullanıcı/organizasyon izolasyonunu doğrular."""
    first = (await register_user(client, "iso-one@example.com")).json()
    second = (await register_user(client, "iso-two@example.com")).json()
    assert first["organization_id"] != second["organization_id"]
