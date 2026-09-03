"""Prometheus metrikleri (API latency, istek sayısı, DB pool)."""

from __future__ import annotations

from fastapi import Request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram
from prometheus_client import generate_latest as _generate_latest

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Toplam HTTP isteği",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP istek süresi",
    ["method", "path"],
)
DB_POOL_IN_USE = Gauge(
    "db_pool_connections_in_use", "Kullanımdaki veritabanı bağlantısı"
)


def _route_template(request: Request) -> str:
    """Kardinaliteyi sınırlamak için UUID'li yol yerine route şablonunu kullanır."""
    route = request.scope.get("route")
    return getattr(route, "path", None) or request.url.path


def observe_request(request: Request, status_code: int, duration: float) -> None:
    path = _route_template(request)
    REQUEST_COUNT.labels(request.method, path, str(status_code)).inc()
    REQUEST_LATENCY.labels(request.method, path).observe(duration)


def render() -> tuple[bytes, str]:
    from app.core.database import engine

    pool = engine.pool
    if hasattr(pool, "checkedout"):
        DB_POOL_IN_USE.set(pool.checkedout())
    return _generate_latest(), CONTENT_TYPE_LATEST
