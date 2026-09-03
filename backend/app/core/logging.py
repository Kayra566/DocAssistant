import logging
import re
from typing import Any

from pythonjsonlogger.json import JsonFormatter

from app.core.config import settings

# Log çıktısında kişisel veri ve sır bırakmamak için maskelenen desenler.
_PII_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<email>"),
    (re.compile(r"(?i)bearer\s+[\w\-._~+/]+=*"), "<redacted>"),
    (re.compile(r"eyJ[\w\-._~+/]+=*"), "<jwt>"),
    (
        re.compile(
            r"(?i)\b(password|token|secret|api[_-]?key|authorization)\b"
            r"(\"?\s*[:=]\s*\"?)([^\s,\"}]+)"
        ),
        r"\1\2<redacted>",
    ),
    (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "<card>"),
)


def mask_pii(text: str) -> str:
    for pattern, replacement in _PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class PIIMaskingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not settings.LOG_PII_MASKING:
            return True
        record.msg = mask_pii(str(record.msg))
        if record.args:
            record.args = tuple(mask_pii(str(a)) for a in record.args)
        return True


def configure_logging() -> None:
    """Structured JSON logging to stdout."""
    handler = logging.StreamHandler()
    formatter = JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)
    handler.addFilter(PIIMaskingFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)


def get_logger(name: str, **context: Any) -> logging.LoggerAdapter:
    return logging.LoggerAdapter(logging.getLogger(name), context)
