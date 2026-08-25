import io

from docx import Document as DocxDocument

from tests.conftest import auth_headers, setup_org


def _txt(content: str = "Merhaba dünya. Bu bir test dokümanıdır.") -> bytes:
    return content.encode("utf-8")


def _docx_bytes(text: str = "Docx içeriği burada.") -> bytes:
    doc = DocxDocument()
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


async def _upload(client, access, org_id, filename, data, content_type="text/plain"):
    return await client.post(
        f"/api/v1/documents/{org_id}/upload",
        headers=auth_headers(access),
        files={"file": (filename, data, content_type)},
    )


async def test_upload_txt_processes_to_ready(client):
    access, org_id = await setup_org(client, "doc-a@example.com")
    resp = await _upload(client, access, org_id, "notes.txt", _txt())
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "ready"
    assert body["chunk_count"] >= 1
    assert body["file_type"] == "txt"


async def test_upload_docx(client):
    access, org_id = await setup_org(client, "doc-docx@example.com")
    resp = await _upload(
        client,
        access,
        org_id,
        "report.docx",
        _docx_bytes("Yapay zeka dokümanı."),
        "application/octet-stream",
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "ready"
    assert resp.json()["file_type"] == "docx"


async def test_extension_content_mismatch_rejected(client):
    access, org_id = await setup_org(client, "doc-bad@example.com")
    # .pdf uzantısı ama içerik düz metin
    resp = await _upload(client, access, org_id, "fake.pdf", _txt(), "application/pdf")
    assert resp.status_code == 422


async def test_unsupported_extension_rejected(client):
    access, org_id = await setup_org(client, "doc-exe@example.com")
    resp = await _upload(client, access, org_id, "malware.exe", b"MZ\x90\x00")
    assert resp.status_code == 422


async def test_empty_file_rejected(client):
    access, org_id = await setup_org(client, "doc-empty@example.com")
    resp = await _upload(client, access, org_id, "empty.txt", b"")
    assert resp.status_code == 422


async def test_list_favorite_and_delete(client):
    access, org_id = await setup_org(client, "doc-list@example.com")
    doc = (await _upload(client, access, org_id, "a.txt", _txt())).json()
    doc_id = doc["id"]

    listed = await client.get(
        f"/api/v1/documents/{org_id}", headers=auth_headers(access)
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    fav = await client.post(
        f"/api/v1/documents/{org_id}/{doc_id}/favorite",
        headers=auth_headers(access),
        json={"is_favorite": True},
    )
    assert fav.json()["is_favorite"] is True

    deleted = await client.delete(
        f"/api/v1/documents/{org_id}/{doc_id}", headers=auth_headers(access)
    )
    assert deleted.status_code == 204

    listed2 = await client.get(
        f"/api/v1/documents/{org_id}", headers=auth_headers(access)
    )
    assert listed2.json() == []


async def test_signed_download_roundtrip(client):
    access, org_id = await setup_org(client, "doc-dl@example.com")
    content = "İndirilecek gizli içerik."
    doc = (await _upload(client, access, org_id, "secret.txt", _txt(content))).json()

    url_resp = await client.get(
        f"/api/v1/documents/{org_id}/{doc['id']}/download-url",
        headers=auth_headers(access),
    )
    assert url_resp.status_code == 200
    url = url_resp.json()["url"]

    # İmzalı URL auth gerektirmeden çalışır
    dl = await client.get(url)
    assert dl.status_code == 200
    assert dl.content.decode("utf-8") == content


async def test_download_requires_valid_token(client):
    resp = await client.get("/api/v1/documents/download?token=bogus")
    assert resp.status_code == 401


async def test_batch_upload_partial(client):
    access, org_id = await setup_org(client, "doc-batch@example.com")
    resp = await client.post(
        f"/api/v1/documents/{org_id}/batch-upload",
        headers=auth_headers(access),
        files=[
            ("files", ("ok.txt", _txt(), "text/plain")),
            ("files", ("bad.pdf", _txt(), "application/pdf")),
        ],
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["uploaded"]) == 1
    assert len(body["errors"]) == 1


async def test_document_tenant_isolation(client):
    a_access, a_org = await setup_org(client, "tenant-doc-a@example.com")
    _, b_org = await setup_org(client, "tenant-doc-b@example.com")
    await _upload(client, a_access, a_org, "a.txt", _txt())

    # A, B'nin dokümanlarını listeleyemez (üye değil → 403)
    resp = await client.get(
        f"/api/v1/documents/{b_org}", headers=auth_headers(a_access)
    )
    assert resp.status_code == 403
