from tests.conftest import (
    auth_headers,
    login_user,
    register_user,
)


async def test_register_creates_user_and_org(client):
    resp = await register_user(client, "a@example.com", full_name="Ada")
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["email"] == "a@example.com"
    assert data["user"]["is_verified"] is False
    assert data["organization_id"]
    assert data["dev_verification_token"]


async def test_register_rejects_weak_password(client):
    resp = await register_user(client, "weak@example.com", password="12345678")
    assert resp.status_code == 422


async def test_register_duplicate_email(client):
    await register_user(client, "dup@example.com")
    resp = await register_user(client, "dup@example.com")
    assert resp.status_code == 409


async def test_verify_email_flow(client):
    reg = (await register_user(client, "v@example.com")).json()
    resp = await client.post(
        "/api/v1/auth/verify-email",
        json={"token": reg["dev_verification_token"]},
    )
    assert resp.status_code == 200

    login = await login_user(client, "v@example.com")
    access = login.json()["access_token"]
    me = await client.get("/api/v1/auth/me", headers=auth_headers(access))
    assert me.json()["is_verified"] is True


async def test_login_returns_tokens(client):
    await register_user(client, "l@example.com")
    resp = await login_user(client, "l@example.com")
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"] and body["refresh_token"]


async def test_login_wrong_password(client):
    await register_user(client, "w@example.com")
    resp = await login_user(client, "w@example.com", password="wrong-password-xyz")
    assert resp.status_code == 401


async def test_account_lockout_after_5_failures(client):
    await register_user(client, "lock@example.com")
    for _ in range(5):
        await login_user(client, "lock@example.com", password="bad-password-000")
    # 6. deneme doğru parolayla bile kilitli olmalı
    resp = await login_user(client, "lock@example.com")
    assert resp.status_code == 423


async def test_refresh_rotation_and_reuse_detection(client):
    await register_user(client, "r@example.com")
    login = (await login_user(client, "r@example.com")).json()
    old_refresh = login["refresh_token"]

    r1 = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert r1.status_code == 200
    new_refresh = r1.json()["refresh_token"]
    assert new_refresh != old_refresh

    # Eski (rotasyona uğramış) token yeniden kullanılırsa reddedilir.
    reuse = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
    )
    assert reuse.status_code == 401

    # Reuse tespiti tüm oturumları kapattığı için yeni token da geçersizdir.
    after = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": new_refresh}
    )
    assert after.status_code == 401


async def test_password_reset_flow(client):
    await register_user(client, "reset@example.com")
    forgot = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "reset@example.com"}
    )
    token = forgot.json()["dev_token"]
    assert token

    new_pw = "N3w!Str0ng&Pass99"
    resp = await client.post(
        "/api/v1/auth/reset-password", json={"token": token, "new_password": new_pw}
    )
    assert resp.status_code == 200

    # Eski parola artık çalışmamalı, yenisi çalışmalı.
    assert (await login_user(client, "reset@example.com")).status_code == 401
    assert (
        await login_user(client, "reset@example.com", password=new_pw)
    ).status_code == 200


async def test_forgot_password_unknown_email_no_leak(client):
    resp = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "ghost@example.com"}
    )
    assert resp.status_code == 200
    assert resp.json()["dev_token"] is None


async def test_2fa_requires_pro_plan(client):
    await register_user(client, "free@example.com")
    access = (await login_user(client, "free@example.com")).json()["access_token"]
    resp = await client.post("/api/v1/auth/2fa/enable", headers=auth_headers(access))
    assert resp.status_code == 422  # Free planda 2FA kapalı


async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
