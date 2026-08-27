import io
import zipfile

from tests.conftest import auth_headers, setup_org

DOC_TEXT = (
    "Sözleşme 01.03.2025 tarihinde imzalandı. Toplam bedel 250000 TL'dir. "
    "Yüklenici Ahmet Demir sorumludur. Teslim süresi 90 gündür."
)


async def _setup(client, email):
    access, org_id = await setup_org(client, email)
    doc = (
        await client.post(
            f"/api/v1/documents/{org_id}/upload",
            headers=auth_headers(access),
            files={"file": ("sozlesme.txt", DOC_TEXT.encode("utf-8"), "text/plain")},
        )
    ).json()
    return access, org_id, doc


async def _summary_job(client, access, org_id, doc_id):
    return (
        await client.post(
            f"/api/v1/ai/{org_id}/summary",
            headers=auth_headers(access),
            json={"document_id": doc_id, "level": "short"},
        )
    ).json()


async def _export(client, access, org_id, job_id, fmt):
    return await client.post(
        f"/api/v1/exports/{org_id}",
        headers=auth_headers(access),
        json={"ai_job_id": job_id, "format": fmt},
    )


async def test_export_all_formats_produce_downloadable_files(client):
    access, org_id, doc = await _setup(client, "export-a@example.com")
    job = await _summary_job(client, access, org_id, doc["id"])

    signatures = {
        "pdf": b"%PDF-",
        "docx": b"PK\x03\x04",
        "xlsx": b"PK\x03\x04",
        "md": b"# ",
    }
    for fmt, signature in signatures.items():
        created = await _export(client, access, org_id, job["id"], fmt)
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["status"] == "done", body
        assert body["size_bytes"] > 0
        assert body["filename"].endswith(f".{fmt}")

        downloaded = await client.get(
            f"/api/v1/exports/{org_id}/{body['id']}/download",
            headers=auth_headers(access),
        )
        assert downloaded.status_code == 200
        assert downloaded.content.startswith(signature)


async def test_markdown_export_contains_result_text(client):
    access, org_id, doc = await _setup(client, "export-b@example.com")
    job = await _summary_job(client, access, org_id, doc["id"])
    export = (await _export(client, access, org_id, job["id"], "md")).json()

    downloaded = await client.get(
        f"/api/v1/exports/{org_id}/{export['id']}/download",
        headers=auth_headers(access),
    )
    text = downloaded.content.decode("utf-8")
    assert text.startswith("# Özet")
    assert "sozlesme.txt" in text


async def test_quiz_export_to_xlsx_contains_questions(client):
    access, org_id, doc = await _setup(client, "export-c@example.com")
    job = (
        await client.post(
            f"/api/v1/ai/{org_id}/quiz",
            headers=auth_headers(access),
            json={"document_id": doc["id"], "question_count": 3},
        )
    ).json()
    export = (await _export(client, access, org_id, job["id"], "xlsx")).json()
    assert export["status"] == "done", export

    downloaded = await client.get(
        f"/api/v1/exports/{org_id}/{export['id']}/download",
        headers=auth_headers(access),
    )
    with zipfile.ZipFile(io.BytesIO(downloaded.content)) as archive:
        assert "xl/workbook.xml" in archive.namelist()


async def test_export_requires_completed_job(client):
    access, org_id, _ = await _setup(client, "export-d@example.com")
    resp = await _export(
        client, access, org_id, "00000000-0000-0000-0000-000000000000", "pdf"
    )
    assert resp.status_code == 404


async def test_other_org_cannot_download_export(client):
    access, org_id, doc = await _setup(client, "export-owner@example.com")
    job = await _summary_job(client, access, org_id, doc["id"])
    export = (await _export(client, access, org_id, job["id"], "md")).json()

    outsider, _ = await setup_org(client, "export-outsider@example.com")
    resp = await client.get(
        f"/api/v1/exports/{org_id}/{export['id']}/download",
        headers=auth_headers(outsider),
    )
    assert resp.status_code == 403


async def test_exports_listed_for_job(client):
    access, org_id, doc = await _setup(client, "export-list@example.com")
    job = await _summary_job(client, access, org_id, doc["id"])
    await _export(client, access, org_id, job["id"], "md")
    await _export(client, access, org_id, job["id"], "pdf")

    resp = await client.get(
        f"/api/v1/exports/{org_id}",
        headers=auth_headers(access),
        params={"ai_job_id": job["id"]},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2
