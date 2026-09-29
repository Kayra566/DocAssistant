import app.ai.embeddings as embeddings_module
from app.core.config import settings
from tests.conftest import auth_headers, setup_org

DOC = (
    "Sozlesme 01.03.2025 tarihinde imzalandi. Toplam bedel 250000 TL. "
    "Teslim suresi 90 gundur."
)


async def _setup(client, email):
    access, org_id = await setup_org(client, email)
    await client.post(
        f"/api/v1/documents/{org_id}/upload",
        headers=auth_headers(access),
        files={"file": ("sozlesme.txt", DOC.encode("utf-8"), "text/plain")},
    )
    return access, org_id


async def test_index_status_reports_healthy_index(client):
    access, org_id = await _setup(client, "reindex-a@example.com")

    resp = await client.get(
        f"/api/v1/models/{org_id}/index", headers=auth_headers(access)
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["total_chunks"] >= 1
    assert body["stale_chunks"] == 0
    assert body["needs_reindex"] is False
    assert body["provider"] == "hashing"
    assert body["dimension"] == settings.EMBEDDING_DIM


async def test_dimension_change_is_detected_and_repaired(client, monkeypatch):
    access, org_id = await _setup(client, "reindex-b@example.com")

    # Embedding sağlayıcısını değiştirmiş gibi boyutu büyüt.
    monkeypatch.setattr(settings, "EMBEDDING_DIM", 128)
    embeddings_module.reset_embedder()

    stale = (
        await client.get(
            f"/api/v1/models/{org_id}/index", headers=auth_headers(access)
        )
    ).json()
    assert stale["dimension"] == 128
    assert stale["stale_chunks"] == stale["total_chunks"]
    assert stale["needs_reindex"] is True

    rebuilt = await client.post(
        f"/api/v1/models/{org_id}/index/rebuild", headers=auth_headers(access)
    )
    assert rebuilt.status_code == 200, rebuilt.text
    assert rebuilt.json()["reindexed"] == stale["total_chunks"]

    healthy = (
        await client.get(
            f"/api/v1/models/{org_id}/index", headers=auth_headers(access)
        )
    ).json()
    assert healthy["stale_chunks"] == 0
    assert healthy["needs_reindex"] is False


async def test_search_still_works_after_reindex(client, monkeypatch):
    access, org_id = await _setup(client, "reindex-c@example.com")
    doc_id = (
        await client.get(f"/api/v1/documents/{org_id}", headers=auth_headers(access))
    ).json()[0]["id"]

    monkeypatch.setattr(settings, "EMBEDDING_DIM", 96)
    embeddings_module.reset_embedder()
    await client.post(
        f"/api/v1/models/{org_id}/index/rebuild", headers=auth_headers(access)
    )

    answer = await client.post(
        f"/api/v1/ai/{org_id}/chat",
        headers=auth_headers(access),
        json={"document_id": doc_id, "question": "Toplam bedel nedir?"},
    )
    assert answer.status_code == 200, answer.text
    assert answer.json()["citations"]


async def test_index_endpoints_require_owner(client):
    _, org_id = await _setup(client, "reindex-owner@example.com")
    outsider, _ = await setup_org(client, "reindex-outsider@example.com")

    assert (
        await client.get(
            f"/api/v1/models/{org_id}/index", headers=auth_headers(outsider)
        )
    ).status_code == 403
    assert (
        await client.post(
            f"/api/v1/models/{org_id}/index/rebuild", headers=auth_headers(outsider)
        )
    ).status_code == 403
