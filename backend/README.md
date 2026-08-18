# DocAssistant — Backend

FastAPI tabanlı async backend.

## Kurulum (local, Docker'sız)

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

## Test

```bash
pytest
```

## Migration (Alembic)

```bash
alembic revision --autogenerate -m "mesaj"
alembic upgrade head
```

## Celery worker

```bash
celery -A app.workers.celery_app worker --loglevel=info
```
