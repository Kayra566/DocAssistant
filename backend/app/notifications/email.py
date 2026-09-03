"""Transactional e-posta gönderimi (M11).

Sağlayıcı `EMAIL_PROVIDER` ile seçilir. API anahtarı yoksa gönderim otomatik
olarak konsol sağlayıcısına düşer; böylece local ortam yapılandırma istemez.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    text: str
    html: str


class EmailProvider(Protocol):
    def send(self, message: EmailMessage) -> bool: ...


class ConsoleEmailProvider:
    """Local/test: e-postayı göndermez, yalnızca loglar."""

    def send(self, message: EmailMessage) -> bool:
        logger.info("Email (console) → %s | %s", message.to, message.subject)
        return True


class ResendProvider:
    ENDPOINT = "https://api.resend.com/emails"

    def send(self, message: EmailMessage) -> bool:
        response = httpx.post(
            self.ENDPOINT,
            headers={"Authorization": f"Bearer {settings.EMAIL_API_KEY}"},
            json={
                "from": settings.EMAIL_FROM,
                "to": [message.to],
                "subject": message.subject,
                "text": message.text,
                "html": message.html,
            },
            timeout=settings.EMAIL_TIMEOUT_SECONDS,
        )
        return response.is_success


class SendGridProvider:
    ENDPOINT = "https://api.sendgrid.com/v3/mail/send"

    def send(self, message: EmailMessage) -> bool:
        response = httpx.post(
            self.ENDPOINT,
            headers={"Authorization": f"Bearer {settings.EMAIL_API_KEY}"},
            json={
                "personalizations": [{"to": [{"email": message.to}]}],
                "from": {"email": settings.EMAIL_FROM},
                "subject": message.subject,
                "content": [
                    {"type": "text/plain", "value": message.text},
                    {"type": "text/html", "value": message.html},
                ],
            },
            timeout=settings.EMAIL_TIMEOUT_SECONDS,
        )
        return response.is_success


_provider: EmailProvider | None = None


def get_provider() -> EmailProvider:
    global _provider
    if _provider is None:
        if not settings.EMAIL_API_KEY or settings.EMAIL_PROVIDER == "console":
            _provider = ConsoleEmailProvider()
        elif settings.EMAIL_PROVIDER == "resend":
            _provider = ResendProvider()
        else:
            _provider = SendGridProvider()
    return _provider


def reset_provider() -> None:
    global _provider
    _provider = None


def send(message: EmailMessage) -> bool:
    """Gönderim hatası ana akışı bozmaz; yalnızca loglanır."""
    try:
        return get_provider().send(message)
    except Exception as exc:
        logger.warning("Email gönderilemedi: %s", exc)
        return False
