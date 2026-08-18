# DocAssistant

AI destekli, çok kiracılı (multi-tenant) doküman asistanı SaaS uygulaması.
Dokümanlarınızı yükleyin; RAG ile soru-cevap, özet, quiz, çeviri, veri çıkarma
ve karşılaştırma gibi 7 AI özelliğiyle işleyin.

> **Durum:** Faz 0 — temel iskele. Yol haritası: [docs/ROADMAP.md](docs/ROADMAP.md)

## Teknoloji

| Katman | Teknoloji |
|--------|-----------|
| Backend | FastAPI · async SQLAlchemy · PostgreSQL + pgvector · Alembic |
| Async | Redis · Celery |
| AI | LangChain · Ollama (local LLM) + OpenAI fallback |
| Storage | MinIO (local) / S3 (prod) |
| Frontend | React 18 · TypeScript · Vite · Tailwind · shadcn/ui |
| DevOps | Docker · docker-compose · GitHub Actions |

## Hızlı Başlangıç

### Docker ile (önerilen)

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose -f infra/docker-compose.yml up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- MinIO Console: http://localhost:9001

### Docker'sız (lokal geliştirme)

```bash
# Backend
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload

# Frontend (ayrı terminal)
cd frontend
npm install
npm run dev
```

## Proje Yapısı

```
DocAssistant/
├── backend/     # FastAPI + SQLAlchemy + Celery
├── frontend/    # React + Vite + Tailwind
├── infra/       # docker-compose
├── docs/        # plan, yol haritası, mimari
└── .github/     # CI/CD
```

Detaylar: [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

## Dokümantasyon

- [Proje Planı](docs/PROJECT_PLAN.md)
- [Yol Haritası](docs/ROADMAP.md)
- [Klasör Yapısı](docs/PROJECT_STRUCTURE.md)

## Lisans

Bkz. [LICENSE](LICENSE).