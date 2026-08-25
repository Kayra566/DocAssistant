import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
import pyotp

from app.core.config import settings

ALGORITHM = settings.JWT_ALGORITHM
# bcrypt 72-byte sınırı: parolayı önce SHA-256 ile sabit uzunluğa indiriyoruz.


def _prehash(password: str) -> bytes:
    return hashlib.sha256(password.encode("utf-8")).digest()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prehash(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_prehash(password), hashed.encode("utf-8"))
    except ValueError:
        return False


def _now() -> datetime:
    return datetime.now(UTC)


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    expire = _now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "exp": expire,
        "iat": _now(),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])


def create_download_token(document_id: str) -> str:
    """Kısa ömürlü, imzalı dosya indirme token'ı (signed URL)."""
    payload = {
        "sub": document_id,
        "type": "download",
        "exp": _now() + timedelta(minutes=settings.SIGNED_URL_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def verify_download_token(token: str) -> str:
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
    if payload.get("type") != "download":
        raise ValueError("Geçersiz indirme token türü.")
    return payload["sub"]


def generate_raw_token() -> str:
    """Client'a verilecek ham token (refresh/verification/reset/invite)."""
    return secrets.token_urlsafe(32)


def hash_token(raw: str) -> str:
    """Ham token'ın DB'de saklanacak SHA-256 özeti."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def refresh_expiry() -> datetime:
    return _now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)


# ---------- 2FA (TOTP) ----------
def generate_totp_secret() -> str:
    return pyotp.random_base32()


def totp_provisioning_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=settings.APP_NAME)


def verify_totp(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()
