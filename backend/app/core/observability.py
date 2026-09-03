"""Sentry entegrasyonu — DSN tanımlı değilse tamamen devre dışı kalır."""

from __future__ import annotations

from app.core.config import settings
from app.core.logging import get_logger, mask_pii

logger = get_logger(__name__)


def _scrub(event: dict, hint: dict) -> dict:
    """Sentry'ye giden olaylardan kişisel veriyi temizler."""
    event.pop("user", None)
    request = event.get("request")
    if isinstance(request, dict):
        request.pop("cookies", None)
        request.pop("data", None)
        headers = request.get("headers")
        if isinstance(headers, dict):
            headers.pop("Authorization", None)
            headers.pop("authorization", None)
        if isinstance(request.get("query_string"), str):
            request["query_string"] = mask_pii(request["query_string"])
    return event


def init_sentry() -> bool:
    if not settings.SENTRY_DSN:
        return False
    try:
        import sentry_sdk
    except ImportError:
        logger.warning("SENTRY_DSN tanımlı ancak sentry-sdk kurulu değil.")
        return False

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        release="docassistant@1.0.0",
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        send_default_pii=False,
        before_send=_scrub,
    )
    logger.info("Sentry etkin (%s)", settings.ENVIRONMENT)
    return True
