"""Sabit pencereli rate limiting (memory / Redis backend)."""

from __future__ import annotations

import time
from typing import Protocol

from app.core.config import settings


class RateLimitBackend(Protocol):
    def hit(self, key: str, window_seconds: int) -> int: ...


class MemoryBackend:
    """Tek süreçlik sayaç — local/test için. Prod'da Redis kullanın."""

    def __init__(self) -> None:
        self._counters: dict[str, tuple[int, float]] = {}

    def hit(self, key: str, window_seconds: int) -> int:
        now = time.time()
        count, expires_at = self._counters.get(key, (0, 0.0))
        if now >= expires_at:
            count, expires_at = 0, now + window_seconds
        count += 1
        self._counters[key] = (count, expires_at)
        return count

    def reset(self) -> None:
        self._counters.clear()


class RedisBackend:
    """Çok süreçli dağıtımlar için paylaşımlı sayaç."""

    def __init__(self) -> None:
        import redis

        self._client = redis.Redis.from_url(settings.REDIS_URL)

    def hit(self, key: str, window_seconds: int) -> int:
        pipe = self._client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds, nx=True)
        return int(pipe.execute()[0])


_backend: RateLimitBackend | None = None


def get_backend() -> RateLimitBackend:
    global _backend
    if _backend is None:
        _backend = (
            RedisBackend() if settings.RATE_LIMIT_BACKEND == "redis" else MemoryBackend()
        )
    return _backend


def reset_backend() -> None:
    """Testler arası sayaçları sıfırlamak için."""
    global _backend
    _backend = None


def check(identity: str, bucket: str, limit: int, window_seconds: int) -> int | None:
    """Limit aşıldıysa kalan saniyeyi, aşılmadıysa None döndürür."""
    window = int(time.time()) // window_seconds
    key = f"ratelimit:{bucket}:{identity}:{window}"
    if get_backend().hit(key, window_seconds) > limit:
        return window_seconds - (int(time.time()) % window_seconds)
    return None
