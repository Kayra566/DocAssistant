import app.ai.registry as registry_module
from app.ai.provider import FakeProvider, OllamaProvider, build_provider
from app.core.config import settings
from tests.conftest import auth_headers, setup_org


def _write_gguf(tmp_path, name: str, size: int = 32) -> None:
    (tmp_path / name).write_bytes(b"\x00" * size)


def test_build_provider_maps_model_id():
    assert isinstance(build_provider("builtin:fake"), FakeProvider)

    provider = build_provider("ollama:qwen2.5:7b")
    assert isinstance(provider, OllamaProvider)
    # Model adındaki iki nokta korunmalı.
    assert provider.model == "qwen2.5:7b"


async def test_lists_builtin_when_ollama_unreachable(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MODELS_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:9")

    access, _ = await setup_org(client, "models-a@example.com")
    resp = await client.get("/api/v1/models", headers=auth_headers(access))

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ollama_available"] is False
    assert [m["id"] for m in body["models"]] == ["builtin:fake"]
    assert body["active_model_id"] == "builtin:fake"


async def test_dropped_gguf_file_is_discovered(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MODELS_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:9")
    _write_gguf(tmp_path, "qwen2.5-7b.gguf", 128)

    access, _ = await setup_org(client, "models-b@example.com")
    body = (
        await client.get("/api/v1/models", headers=auth_headers(access))
    ).json()

    dropped = [m for m in body["models"] if m["source"] == "file"]
    assert len(dropped) == 1
    assert dropped[0]["name"] == "qwen2.5-7b"
    assert dropped[0]["size_bytes"] == 128
    # Ollama'ya aktarılmadan kullanıma hazır sayılmaz.
    assert dropped[0]["ready"] is False


async def test_cannot_activate_model_that_is_not_ready(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MODELS_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:9")
    _write_gguf(tmp_path, "hazir-degil.gguf")

    access, org_id = await setup_org(client, "models-c@example.com")
    resp = await client.put(
        f"/api/v1/models/{org_id}/active",
        headers=auth_headers(access),
        json={"model_id": "file:hazir-degil.gguf"},
    )
    assert resp.status_code == 422


async def test_active_model_persists_and_applies(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MODELS_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:9")

    access, org_id = await setup_org(client, "models-d@example.com")
    resp = await client.put(
        f"/api/v1/models/{org_id}/active",
        headers=auth_headers(access),
        json={"model_id": "builtin:fake"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"model_id": "builtin:fake", "configured": True}

    again = await client.get("/api/v1/models/active", headers=auth_headers(access))
    assert again.json()["model_id"] == "builtin:fake"


async def test_switching_model_requires_owner(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MODELS_DIR", str(tmp_path))
    owner, org_id = await setup_org(client, "models-owner@example.com")
    outsider, _ = await setup_org(client, "models-outsider@example.com")

    resp = await client.put(
        f"/api/v1/models/{org_id}/active",
        headers=auth_headers(outsider),
        json={"model_id": "builtin:fake"},
    )
    assert resp.status_code == 403


async def test_import_requires_running_ollama(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MODELS_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:9")
    _write_gguf(tmp_path, "model.gguf")

    access, org_id = await setup_org(client, "models-e@example.com")
    resp = await client.post(
        f"/api/v1/models/{org_id}/import",
        headers=auth_headers(access),
        json={"filename": "model.gguf"},
    )
    assert resp.status_code == 422
    assert "Ollama" in resp.json()["detail"]


async def test_import_rejects_path_traversal(monkeypatch, tmp_path):
    import pytest

    from app.core.exceptions import ValidationError

    monkeypatch.setattr(settings, "MODELS_DIR", str(tmp_path))
    with pytest.raises(ValidationError):
        await registry_module.import_gguf("../../etc/passwd")
