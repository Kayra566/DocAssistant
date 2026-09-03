"""Transactional e-posta şablonları (TR/EN)."""

from __future__ import annotations

from html import escape

from app.core.config import settings
from app.core.i18n import Locale, translate
from app.notifications.email import EmailMessage

_LAYOUT = """<!doctype html>
<html lang="{lang}">
  <body style="font-family:system-ui,sans-serif;background:#0a0a0a;color:#e5e5e5;padding:24px">
    <div style="max-width:520px;margin:0 auto;background:#171717;border-radius:12px;padding:24px">
      <h1 style="font-size:18px;margin:0 0 16px">{title}</h1>
      <p style="font-size:14px;line-height:1.6;margin:0 0 20px">{body}</p>
      {action}
      <p style="font-size:12px;color:#737373;margin:24px 0 0">DocAssistant</p>
    </div>
  </body>
</html>"""

_BUTTON = (
    '<a href="{url}" style="display:inline-block;background:#4f46e5;color:#fff;'
    'padding:10px 18px;border-radius:8px;text-decoration:none;font-size:14px">{label}</a>'
)


def _render(
    *, to: str, subject: str, body: str, url: str | None, label: str, locale: Locale
) -> EmailMessage:
    action = _BUTTON.format(url=escape(url), label=escape(label)) if url else ""
    html = _LAYOUT.format(
        lang=locale, title=escape(subject), body=escape(body), action=action
    )
    text = f"{subject}\n\n{body}" + (f"\n\n{url}" if url else "")
    return EmailMessage(to=to, subject=subject, text=text, html=html)


def _link(path: str, token: str) -> str:
    return f"{settings.FRONTEND_BASE_URL.rstrip('/')}{path}?token={token}"


def verification_email(to: str, token: str, locale: Locale = "tr") -> EmailMessage:
    return _render(
        to=to,
        subject=translate("email.verify.subject", locale),
        body=translate("email.verify.body", locale),
        url=_link("/verify-email", token),
        label="Doğrula" if locale == "tr" else "Verify",
        locale=locale,
    )


def password_reset_email(to: str, token: str, locale: Locale = "tr") -> EmailMessage:
    return _render(
        to=to,
        subject=translate("email.reset.subject", locale),
        body=translate("email.reset.body", locale),
        url=_link("/reset-password", token),
        label="Parolayı sıfırla" if locale == "tr" else "Reset password",
        locale=locale,
    )


def invitation_email(
    to: str, token: str, organization: str, locale: Locale = "tr"
) -> EmailMessage:
    body = f"{organization} · {translate('email.invite.body', locale)}"
    return _render(
        to=to,
        subject=translate("email.invite.subject", locale),
        body=body,
        url=_link("/accept-invite", token),
        label="Daveti kabul et" if locale == "tr" else "Accept invitation",
        locale=locale,
    )


def payment_failed_email(to: str, locale: Locale = "tr") -> EmailMessage:
    return _render(
        to=to,
        subject=translate("email.payment_failed.subject", locale),
        body=translate("email.payment_failed.body", locale),
        url=f"{settings.FRONTEND_BASE_URL.rstrip('/')}/dashboard",
        label="Planı yönet" if locale == "tr" else "Manage plan",
        locale=locale,
    )


def quota_warning_email(to: str, locale: Locale = "tr") -> EmailMessage:
    return _render(
        to=to,
        subject=translate("email.quota_warning.subject", locale),
        body=translate("email.quota_warning.body", locale),
        url=f"{settings.FRONTEND_BASE_URL.rstrip('/')}/dashboard",
        label="Planı yükselt" if locale == "tr" else "Upgrade plan",
        locale=locale,
    )
