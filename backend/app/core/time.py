from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC)


def ensure_utc(dt: datetime | None) -> datetime | None:
    """DB'den okunan datetime'ı timezone-aware UTC'ye normalize eder.

    SQLite (test) naive datetime döndürür; Postgres aware döndürür.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)
