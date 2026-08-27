from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from app.core.config import settings


def cache_key(*parts: str) -> str:
    raw = "::".join(parts)
    return "ai:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


class InMemoryCache:
    def __init__(self):
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if not item:
            return None
        expires, value = item
        if expires < time.time():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        self._store[key] = (time.time() + ttl, value)

    def clear(self) -> None:
        self._store.clear()


class RedisCache:
    def __init__(self):
        import redis

        self.client = redis.Redis.from_url(settings.REDIS_URL)

    def get(self, key: str) -> Any | None:
        raw = self.client.get(key)
        return json.loads(raw) if raw else None

    def set(self, key: str, value: Any, ttl: int) -> None:
        self.client.setex(key, ttl, json.dumps(value))


_cache: InMemoryCache | RedisCache | None = None


def get_cache():
    global _cache
    if _cache is None:
        _cache = (
            RedisCache() if settings.AI_CACHE_BACKEND == "redis" else InMemoryCache()
        )
    return _cache
