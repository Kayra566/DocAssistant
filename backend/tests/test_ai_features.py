from tests.conftest import auth_headers, setup_org

DOC_A = (
    "Sözleşme 01.03.2025 tarihinde imzalanmıştır. Toplam bedel 250000 TL olarak "
    "belirlenmiştir. Yüklenici Ahmet Demir sorumludur. Teslim süresi 90 gündür. "
    "Gecikme halinde günlük 500 TL ceza uygulanır."
)
DOC_B = (
    "Sözleşme 15.06.2025 tarihinde imzalanmıştır. Toplam bedel 310000 TL olarak "
    "güncellenmiştir. Yüklenici Mehmet Kaya sorumludur. Teslim süresi 120 gündür."
)


async def _upload(client, access, org_id, text=DOC_A, filename="sozlesme.txt"):
    resp = await client.post(
        f"/api/v1/documents/{org_id}/upload",
        headers=auth_headers(access),
        files={"file": (filename, text.encode("utf-8"), "text/plain")},
    )
    return resp.json()


async def _setup(client, email):
    access, org_id = await setup_org(client, email)
    doc = await _upload(client, access, org_id)
    return access, org_id, doc


async def test_summary_levels(client):
    access, org_id, doc = await _setup(client, "ai-sum@example.com")
    for level in ("short", "detailed", "bullets", "executive"):
        resp = await client.post(
            f"/api/v1/ai/{org_id}/summary",
            headers=auth_headers(access),
            json={"document_id": doc["id"], "level": level, "preset": "hukuk"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "done"
        assert body["result"]["text"]
        assert body["params"]["level"] == level


async def test_keypoints_returns_structured_fields(client):
    access, org_id, doc = await _setup(client, "ai-kp@example.com")
    resp = await client.post(
        f"/api/v1/ai/{org_id}/keypoints",
        headers=auth_headers(access),
        json={"document_id": doc["id"]},
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()["result"]
    assert set(result) >= {"dates", "names", "numbers", "decisions"}
    assert "01.03.2025" in result["dates"]
    assert any("Ahmet" in n for n in result["names"])


async def test_quiz_generates_requested_questions(client):
    access, org_id, doc = await _setup(client, "ai-quiz@example.com")
    resp = await client.post(
        f"/api/v1/ai/{org_id}/quiz",
        headers=auth_headers(access),
        json={
            "document_id": doc["id"],
            "question_count": 4,
            "question_types": ["multiple_choice", "true_false"],
        },
    )
    assert resp.status_code == 200, resp.text
    questions = resp.json()["result"]["questions"]
    assert len(questions) == 4
    assert {q["type"] for q in questions} == {"multiple_choice", "true_false"}
    assert all(q["question"] for q in questions)


async def test_quiz_rejects_invalid_count(client):
    access, org_id, doc = await _setup(client, "ai-quiz-bad@example.com")
    resp = await client.post(
        f"/api/v1/ai/{org_id}/quiz",
        headers=auth_headers(access),
        json={"document_id": doc["id"], "question_count": 99},
    )
    assert resp.status_code == 422


async def test_translate_preserves_target_language(client):
    access, org_id, doc = await _setup(client, "ai-tr@example.com")
    resp = await client.post(
        f"/api/v1/ai/{org_id}/translate",
        headers=auth_headers(access),
        json={"document_id": doc["id"], "target_language": "İngilizce"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["params"]["target_language"] == "İngilizce"
    assert "İngilizce" in body["result"]["text"]


async def test_extract_returns_records(client):
    access, org_id, doc = await _setup(client, "ai-ex@example.com")
    resp = await client.post(
        f"/api/v1/ai/{org_id}/extract",
        headers=auth_headers(access),
        json={"document_id": doc["id"], "schema_hint": "tarih, bedel, yüklenici"},
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()["result"]
    assert result["columns"]
    assert len(result["records"]) >= 1


async def test_compare_two_documents(client):
    access, org_id, doc_a = await _setup(client, "ai-cmp@example.com")
    doc_b = await _upload(client, access, org_id, DOC_B, "sozlesme-v2.txt")

    resp = await client.post(
        f"/api/v1/ai/{org_id}/compare",
        headers=auth_headers(access),
        json={"document_id": doc_a["id"], "other_document_id": doc_b["id"]},
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()["result"]
    assert set(result) >= {"summary", "only_in_a", "only_in_b", "changed"}
    assert result["summary"]


async def test_compare_requires_existing_second_document(client):
    access, org_id, doc = await _setup(client, "ai-cmp-bad@example.com")
    resp = await client.post(
        f"/api/v1/ai/{org_id}/compare",
        headers=auth_headers(access),
        json={
            "document_id": doc["id"],
            "other_document_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert resp.status_code == 404


async def test_job_is_cached_on_second_run(client):
    access, org_id, doc = await _setup(client, "ai-cache@example.com")
    payload = {"document_id": doc["id"], "level": "short", "preset": "genel"}
    first = (
        await client.post(
            f"/api/v1/ai/{org_id}/summary",
            headers=auth_headers(access),
            json=payload,
        )
    ).json()
    second = (
        await client.post(
            f"/api/v1/ai/{org_id}/summary",
            headers=auth_headers(access),
            json=payload,
        )
    ).json()
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert second["tokens_used"] == 0
    assert second["result"] == first["result"]


async def test_jobs_are_listed_and_retrievable(client):
    access, org_id, doc = await _setup(client, "ai-jobs@example.com")
    created = (
        await client.post(
            f"/api/v1/ai/{org_id}/keypoints",
            headers=auth_headers(access),
            json={"document_id": doc["id"]},
        )
    ).json()

    listed = await client.get(
        f"/api/v1/ai/{org_id}/jobs?document_id={doc['id']}&type=keypoints",
        headers=auth_headers(access),
    )
    assert listed.status_code == 200
    assert [j["id"] for j in listed.json()] == [created["id"]]

    single = await client.get(
        f"/api/v1/ai/{org_id}/jobs/{created['id']}", headers=auth_headers(access)
    )
    assert single.status_code == 200
    assert single.json()["type"] == "keypoints"


async def test_jobs_are_tenant_isolated(client):
    access_a, org_a, doc_a = await _setup(client, "ai-iso-a@example.com")
    job = (
        await client.post(
            f"/api/v1/ai/{org_a}/summary",
            headers=auth_headers(access_a),
            json={"document_id": doc_a["id"]},
        )
    ).json()

    access_b, org_b = await setup_org(client, "ai-iso-b@example.com")
    resp = await client.get(
        f"/api/v1/ai/{org_b}/jobs/{job['id']}", headers=auth_headers(access_b)
    )
    assert resp.status_code == 404


async def test_prompt_presets_endpoint(client):
    resp = await client.get("/api/v1/ai/prompt-presets")
    assert resp.status_code == 200
    body = resp.json()
    assert {p["key"] for p in body["presets"]} == {"genel", "hukuk", "akademik", "is"}
    assert {p["key"] for p in body["summary_levels"]} == {
        "short",
        "detailed",
        "bullets",
        "executive",
    }
