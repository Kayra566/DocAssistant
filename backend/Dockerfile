# syntax=docker/dockerfile:1

# ---------- base ----------
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

# ---------- deps ----------
# Yalnızca runtime bağımlılıkları; dev araçları prod imajına girmez.
FROM base AS deps
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install "."

# ---------- runtime ----------
FROM base AS runtime
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY . .

# Root olmayan kullanıcı: konteyner ele geçirilse bile yetki yükseltmeyi zorlaştırır.
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/_storage \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
