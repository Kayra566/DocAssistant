from app.notifications import email as email_module
from app.notifications import templates
from tests.conftest import auth_headers, register_user, setup_org


class RecordingProvider:
    def __init__(self) -> None:
        self.sent: list[email_module.EmailMessage] = []

    def send(self, message: email_module.EmailMessage) -> bool:
        self.sent.append(message)
        return True


def _record(monkeypatch) -> RecordingProvider:
    provider = RecordingProvider()
    monkeypatch.setattr(email_module, "_provider", provider)
    return provider


def test_console_provider_is_default_without_api_key():
    email_module.reset_provider()
    assert isinstance(email_module.get_provider(), email_module.ConsoleEmailProvider)


def test_send_swallows_provider_errors(monkeypatch):
    class Broken:
        def send(self, message):
            raise RuntimeError("smtp down")

    monkeypatch.setattr(email_module, "_provider", Broken())
    assert email_module.send(templates.verification_email("a@b.com", "tok")) is False


def test_templates_are_localized_and_escape_content():
    tr = templates.verification_email("a@b.com", "tok", "tr")
    en = templates.verification_email("a@b.com", "tok", "en")

    assert tr.subject == "DocAssistant hesabınızı doğrulayın"
    assert en.subject == "Verify your DocAssistant account"
    assert "tok" in tr.text
    assert "<html" in tr.html


def test_invitation_template_includes_organization():
    message = templates.invitation_email("a@b.com", "tok", "Acme A.Ş.")
    assert "Acme" in message.text


async def test_register_sends_verification_email(client, monkeypatch):
    provider = _record(monkeypatch)
    await register_user(client, "notify-reg@example.com")

    assert len(provider.sent) == 1
    assert provider.sent[0].to == "notify-reg@example.com"


async def test_forgot_password_sends_email_only_for_known_user(client, monkeypatch):
    await register_user(client, "notify-reset@example.com")
    provider = _record(monkeypatch)

    await client.post(
        "/api/v1/auth/forgot-password", json={"email": "notify-reset@example.com"}
    )
    await client.post(
        "/api/v1/auth/forgot-password", json={"email": "yok@example.com"}
    )

    assert [m.to for m in provider.sent] == ["notify-reset@example.com"]


async def test_invite_sends_email(client, monkeypatch):
    access, org_id = await setup_org(client, "notify-owner@example.com")
    provider = _record(monkeypatch)

    await client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers=auth_headers(access),
        json={"email": "davetli@example.com", "role": "member"},
    )

    assert provider.sent[-1].to == "davetli@example.com"


async def test_welcome_notification_created_on_register(client):
    reg = await register_user(client, "notify-inapp@example.com")
    assert reg.status_code == 201

    access = (
        await client.post(
            "/api/v1/auth/login",
            json={
                "email": "notify-inapp@example.com",
                "password": "Tr0ub4dour&3xample!",
            },
        )
    ).json()["access_token"]

    listed = await client.get("/api/v1/notifications", headers=auth_headers(access))
    assert listed.status_code == 200
    body = listed.json()
    assert len(body) == 1
    assert body[0]["type"] == "welcome"
    assert body[0]["read"] is False

    count = await client.get(
        "/api/v1/notifications/unread-count", headers=auth_headers(access)
    )
    assert count.json()["unread"] == 1


async def test_mark_notification_read(client):
    access, _ = await setup_org(client, "notify-read@example.com")
    notification = (
        await client.get("/api/v1/notifications", headers=auth_headers(access))
    ).json()[0]

    marked = await client.post(
        f"/api/v1/notifications/{notification['id']}/read",
        headers=auth_headers(access),
    )
    assert marked.status_code == 200
    assert marked.json()["read"] is True

    count = await client.get(
        "/api/v1/notifications/unread-count", headers=auth_headers(access)
    )
    assert count.json()["unread"] == 0


async def test_notifications_are_user_scoped(client):
    first_access, _ = await setup_org(client, "notify-a@example.com")
    second_access, _ = await setup_org(client, "notify-b@example.com")

    first_id = (
        await client.get("/api/v1/notifications", headers=auth_headers(first_access))
    ).json()[0]["id"]

    resp = await client.post(
        f"/api/v1/notifications/{first_id}/read", headers=auth_headers(second_access)
    )
    assert resp.status_code == 404


async def test_mark_all_read(client):
    access, _ = await setup_org(client, "notify-all@example.com")

    resp = await client.post(
        "/api/v1/notifications/read-all", headers=auth_headers(access)
    )
    assert resp.status_code == 200
    assert resp.json()["unread"] == 0
