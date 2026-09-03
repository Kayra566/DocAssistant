"""Hassas alanlar için AES-256-GCM şifreleme (encryption at rest)."""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import String, TypeDecorator

from app.core.config import settings

_PREFIX = "enc:v1:"
_NONCE_BYTES = 12


def _key() -> bytes:
    """32 baytlık anahtar. ENCRYPTION_KEY yoksa JWT_SECRET'ten türetilir."""
    material = settings.ENCRYPTION_KEY or settings.JWT_SECRET
    return hashlib.sha256(material.encode("utf-8")).digest()


def encrypt(plaintext: str) -> str:
    nonce = os.urandom(_NONCE_BYTES)
    ciphertext = AESGCM(_key()).encrypt(nonce, plaintext.encode("utf-8"), None)
    return _PREFIX + base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")


def decrypt(value: str) -> str:
    if not value.startswith(_PREFIX):
        # Şifrelemeden önce yazılmış kayıtlar düz metin olarak okunur.
        return value
    raw = base64.urlsafe_b64decode(value[len(_PREFIX) :].encode("ascii"))
    nonce, ciphertext = raw[:_NONCE_BYTES], raw[_NONCE_BYTES:]
    return AESGCM(_key()).decrypt(nonce, ciphertext, None).decode("utf-8")


class EncryptedString(TypeDecorator):
    """DB'ye şifreli yazan, okurken çözen string kolonu."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        return encrypt(value) if value else value

    def process_result_value(self, value: str | None, dialect) -> str | None:
        return decrypt(value) if value else value
