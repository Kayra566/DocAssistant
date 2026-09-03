"""HTTP middleware'leri: güvenlik başlıkları, rate limiting, istek metrikleri."""

from __future__ import annotations

import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core import ratelimit
from app.core.config import settings

# Sağlık/metrik uçları limitin ve gövde işlemenin dışında tutulur.
EXEMPT_PATHS = frozenset({"/", "/docs", "/health", "/ready", "/metrics"})


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if not settings.SECURITY_HEADERS_ENABLED:
            return response

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        response.headers.setdefault("Content-Security-Policy", settings.CSP_POLICY)
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if settings.ENVIRONMENT == "production":
            response.headers.setdefault(
                "Strict-Transport-Security",
                f"max-age={settings.HSTS_MAX_AGE}; includeSubDomains",
            )
        return response


def _identity(request: Request) -> str:
    """Oturum açmış kullanıcıyı token'dan, aksi halde istemci IP'sini kullanır."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        from app.core import security

        try:
            payload = security.decode_token(auth.split(" ", 1)[1].strip())
            return f"user:{payload.get('sub')}"
        except Exception:
            pass
    forwarded = request.headers.get("x-forwarded-for", "")
    client_ip = forwarded.split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )
    return f"ip:{client_ip}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED or request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        is_auth = request.url.path.startswith(f"{settings.API_V1_PREFIX}/auth/")
        limit, window, bucket = (
            (
                settings.RATE_LIMIT_AUTH_REQUESTS,
                settings.RATE_LIMIT_AUTH_WINDOW_SECONDS,
                "auth",
            )
            if is_auth
            else (
                settings.RATE_LIMIT_REQUESTS,
                settings.RATE_LIMIT_WINDOW_SECONDS,
                "api",
            )
        )

        retry_after = ratelimit.check(_identity(request), bucket, limit, window)
        if retry_after is not None:
            return JSONResponse(
                status_code=429,
                content={"detail": "Çok fazla istek gönderildi. Lütfen bekleyin."},
                headers={"Retry-After": str(retry_after)},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.METRICS_ENABLED:
            return await call_next(request)

        from app.core.metrics import observe_request

        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            observe_request(request, 500, time.perf_counter() - started)
            raise
        observe_request(request, response.status_code, time.perf_counter() - started)
        return response
