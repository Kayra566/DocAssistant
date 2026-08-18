async def test_health(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_ready(client):
    resp = await client.get("/api/v1/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json()["docs"] == "/docs"
