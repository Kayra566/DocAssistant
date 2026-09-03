async def test_health(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_ready(client):
    resp = await client.get("/api/v1/ready")
    assert resp.status_code == 200
    body = resp.json()
    # Redis test ortamında çalışmıyor; DB erişilebilir olmalı.
    assert body["database"] == "up"
    assert body["status"] in {"ready", "degraded"}


async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json()["docs"] == "/docs"
