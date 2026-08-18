# DocAssistant — Proje Klasör Yapısı

> Bu belge projenin detaylı dosya/klasör organizasyonunu tanımlar.
> Monorepo yapısı: `backend/`, `frontend/`, `infra/`, `docs/`.

---

## Tam Yapı

```
DocAssistant/
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Lint + test + build
│       ├── deploy-staging.yml      # Staging otomatik deploy
│       └── deploy-production.yml   # Production manuel onay
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app + middleware
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py       # Ana router (tüm endpoint'leri topla)
│   │   │       ├── auth.py         # /auth (register/login/verify/reset/2fa)
│   │   │       ├── organizations.py # /organizations + /memberships
│   │   │       ├── documents.py    # /documents (upload/list/delete/favorite)
│   │   │       ├── ai.py           # /ai (chat/summary/quiz/translate vb.)
│   │   │       ├── billing.py      # /billing (stripe checkout/portal/webhook)
│   │   │       ├── sharing.py      # /share (links + ekip paylaşımı)
│   │   │       ├── analytics.py    # /analytics (dashboard + metrics)
│   │   │       ├── export.py       # /export (PDF/DOCX/XLSX)
│   │   │       └── admin.py        # /admin (platform yönetimi)
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # Pydantic Settings (env yönetimi)
│   │   │   ├── security.py         # JWT + password hashing + 2FA
│   │   │   ├── database.py         # SQLAlchemy engine + session factory
│   │   │   ├── redis.py            # Redis client
│   │   │   ├── storage.py          # S3/MinIO adapter (signed URL)
│   │   │   ├── logging.py          # Structured JSON logging
│   │   │   ├── rate_limit.py       # Rate limiting decorator (Redis)
│   │   │   └── exceptions.py       # Custom exception'lar
│   │   │
│   │   ├── models/                 # SQLAlchemy modelleri
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Base model (id, created_at, updated_at)
│   │   │   ├── user.py             # User, VerificationToken, PasswordResetToken
│   │   │   ├── organization.py     # Organization, Membership, Invitation
│   │   │   ├── document.py         # Document, DocumentChunk
│   │   │   ├── ai.py               # AIJob
│   │   │   ├── billing.py          # Subscription, UsageRecord, StripeEvent
│   │   │   ├── sharing.py          # ShareLink, Comment
│   │   │   └── audit.py            # AuditLog
│   │   │
│   │   ├── schemas/                # Pydantic modelleri (request/response)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # RegisterRequest, LoginResponse vb.
│   │   │   ├── organization.py
│   │   │   ├── document.py
│   │   │   ├── ai.py
│   │   │   ├── billing.py
│   │   │   └── common.py           # Paginated, ErrorResponse
│   │   │
│   │   ├── repositories/           # Veri erişim katmanı (tenant-scoped)
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # BaseRepository (tenant scoping)
│   │   │   ├── user.py
│   │   │   ├── organization.py
│   │   │   ├── document.py
│   │   │   ├── ai.py
│   │   │   └── billing.py
│   │   │
│   │   ├── services/               # İş mantığı
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Register, login, verify, reset, 2FA
│   │   │   ├── organization.py     # Org/ekip yönetimi, davetler
│   │   │   ├── document.py         # Upload, list, delete, favori
│   │   │   ├── quota.py            # Kota kontrolü + usage tracking
│   │   │   ├── billing.py          # Stripe işlemleri
│   │   │   ├── sharing.py          # Link + ekip paylaşımı
│   │   │   └── export.py           # Export işlemleri
│   │   │
│   │   ├── ai/                     # AI servisleri
│   │   │   ├── __init__.py
│   │   │   ├── provider.py         # LLMProvider arayüzü + Ollama/OpenAI impl.
│   │   │   ├── embeddings.py       # Embedding modeli (sentence-transformers)
│   │   │   ├── vector_store.py     # pgvector işlemleri
│   │   │   ├── rag.py              # RAG orchestration
│   │   │   ├── summary.py          # Summary servisi
│   │   │   ├── keypoints.py        # Key points extraction
│   │   │   ├── quiz.py             # Quiz generation
│   │   │   ├── translation.py      # Translation servisi
│   │   │   ├── extraction.py       # Data extraction
│   │   │   ├── compare.py          # Document compare
│   │   │   ├── prompts/            # Prompt template'leri
│   │   │   │   ├── chat.py
│   │   │   │   ├── summary.py
│   │   │   │   ├── quiz.py
│   │   │   │   └── templates/      # Preset'ler (hukuk/akademik/iş)
│   │   │   └── guards.py           # Prompt injection + moderation
│   │   │
│   │   ├── workers/                # Celery task'ları
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py       # Celery instance
│   │   │   ├── document_tasks.py   # İşleme: metin çıkarma, OCR, chunk, embed
│   │   │   ├── ai_tasks.py         # Uzun AI işleri (summary, quiz vb.)
│   │   │   ├── email_tasks.py      # Email gönderimi
│   │   │   └── billing_tasks.py    # Stripe reconciliation
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── file_validator.py   # Magic bytes + boyut kontrolü
│   │       ├── text_extractor.py   # PDF/DOCX/XLSX/TXT → metin
│   │       ├── ocr.py              # Tesseract / Azure OCR
│   │       ├── chunking.py         # LangChain chunking + sayfa eşleme
│   │       ├── email.py            # Email gönderim (Resend/SendGrid)
│   │       └── crypto.py           # AES-256 encryption
│   │
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/               # Migration dosyaları
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py             # pytest fixtures
│   │   ├── test_auth.py
│   │   ├── test_organizations.py
│   │   ├── test_documents.py
│   │   ├── test_ai_rag.py
│   │   ├── test_billing.py
│   │   ├── test_tenant_isolation.py # Kritik: tenant izolasyon testi
│   │   └── integration/            # Integration testler
│   │       ├── test_upload_flow.py
│   │       └── test_payment_flow.py
│   │
│   ├── Dockerfile                  # Multi-stage (dev + prod)
│   ├── pyproject.toml              # Poetry / Rye dependency yönetimi
│   ├── poetry.lock
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── public/
│   │   ├── favicon.ico
│   │   └── locales/                # i18n dosyaları
│   │       ├── tr.json
│   │       └── en.json
│   │
│   ├── src/
│   │   ├── main.tsx                # React root
│   │   ├── App.tsx                 # Router + layout
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn/ui component'leri
│   │   │   │   ├── button.tsx
│   │   │   │   ├── dialog.tsx
│   │   │   │   ├── dropdown-menu.tsx
│   │   │   │   ├── form.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── toast.tsx
│   │   │   │   └── ...
│   │   │   │
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Footer.tsx
│   │   │   │
│   │   │   └── shared/             # Ortak component'ler
│   │   │       ├── LoadingSpinner.tsx
│   │   │       ├── ErrorBoundary.tsx
│   │   │       └── ProtectedRoute.tsx
│   │   │
│   │   ├── features/               # Feature-based organizasyon
│   │   │   ├── auth/
│   │   │   │   ├── components/     # LoginForm, RegisterForm vb.
│   │   │   │   ├── hooks/          # useAuth, useLogin
│   │   │   │   └── api/            # authApi (TanStack Query)
│   │   │   │
│   │   │   ├── documents/
│   │   │   │   ├── components/     # DocumentList, UploadZone, DocumentCard
│   │   │   │   ├── hooks/          # useDocuments, useUpload
│   │   │   │   └── api/
│   │   │   │
│   │   │   ├── ai/
│   │   │   │   ├── components/     # ChatInterface, SummaryPanel, QuizCard
│   │   │   │   ├── hooks/          # useChat, useSummary
│   │   │   │   └── api/
│   │   │   │
│   │   │   ├── billing/
│   │   │   │   ├── components/     # PricingTable, UpgradeModal
│   │   │   │   ├── hooks/
│   │   │   │   └── api/
│   │   │   │
│   │   │   ├── dashboard/
│   │   │   │   ├── components/     # UsageChart, QuotaBar
│   │   │   │   └── hooks/
│   │   │   │
│   │   │   └── organizations/
│   │   │       ├── components/     # TeamSettings, InviteModal
│   │   │       └── hooks/
│   │   │
│   │   ├── routes/                 # Sayfa component'leri (react-router)
│   │   │   ├── index.tsx           # Route tanımları
│   │   │   ├── HomePage.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── DocumentsPage.tsx
│   │   │   ├── DocumentDetailPage.tsx
│   │   │   ├── ChatPage.tsx
│   │   │   ├── BillingPage.tsx
│   │   │   ├── SettingsPage.tsx
│   │   │   └── NotFoundPage.tsx
│   │   │
│   │   ├── stores/                 # Zustand store'ları
│   │   │   ├── authStore.ts
│   │   │   ├── documentStore.ts
│   │   │   └── uiStore.ts          # Theme, sidebar toggle vb.
│   │   │
│   │   ├── hooks/                  # Global hooks
│   │   │   ├── useApi.ts           # Axios instance + interceptors
│   │   │   ├── useTheme.ts
│   │   │   └── useToast.ts
│   │   │
│   │   ├── lib/                    # Utility'ler
│   │   │   ├── api-client.ts       # Axios config
│   │   │   ├── query-client.ts     # TanStack Query config
│   │   │   ├── utils.ts            # cn (clsx + tailwind-merge)
│   │   │   ├── validators.ts       # Zod schema'ları
│   │   │   └── i18n.ts             # react-i18next config
│   │   │
│   │   ├── types/
│   │   │   ├── api.ts              # API response tipleri
│   │   │   └── models.ts           # Domain modelleri
│   │   │
│   │   └── styles/
│   │       └── globals.css         # Tailwind imports + custom styles
│   │
│   ├── tests/
│   │   ├── setup.ts                # Vitest config
│   │   ├── components/             # Component testleri
│   │   └── e2e/                    # Playwright E2E testleri
│   │       ├── auth.spec.ts
│   │       ├── upload.spec.ts
│   │       └── chat.spec.ts
│   │
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── .env.example
│   └── README.md
│
├── infra/
│   ├── docker/
│   │   ├── backend.Dockerfile      # Backend multi-stage
│   │   ├── frontend.Dockerfile     # Frontend multi-stage (nginx serve)
│   │   └── worker.Dockerfile       # Celery worker
│   │
│   ├── docker-compose.yml          # Local dev ortamı
│   ├── docker-compose.prod.yml     # Production override
│   │
│   ├── k8s/                        # Kubernetes manifests (opsiyonel)
│   │   ├── backend-deployment.yml
│   │   ├── frontend-deployment.yml
│   │   ├── postgres-statefulset.yml
│   │   ├── redis-deployment.yml
│   │   └── ingress.yml
│   │
│   └── scripts/
│       ├── init-db.sh              # Postgres init script
│       ├── backup.sh               # Backup script
│       └── restore.sh              # Restore script
│
├── docs/
│   ├── PROJECT_PLAN.md             # Ana plan
│   ├── ROADMAP.md                  # Faz bazlı yol haritası (bu dosya)
│   ├── PROJECT_STRUCTURE.md        # Klasör yapısı (bu dosya)
│   ├── DEPLOYMENT.md               # Production kurulum rehberi
│   ├── TROUBLESHOOTING.md          # Sık sorunlar + çözümler
│   ├── API.md                      # API dokümantasyonu (ek olarak Swagger)
│   ├── ARCHITECTURE.md             # Mimari detaylar + diyagramlar
│   └── SECURITY.md                 # Güvenlik politikaları
│
├── .gitignore
├── .pre-commit-config.yaml         # pre-commit hooks
├── .editorconfig
├── LICENSE
└── README.md                       # Proje ana README
```

---

## Backend Detayları

### `/app/api/v1/` — Router Organizasyonu

Her endpoint grubu kendi dosyasında:
- **auth.py:** `/auth/register`, `/auth/login`, `/auth/verify`, `/auth/reset`, `/auth/2fa`
- **organizations.py:** `/orgs`, `/orgs/{id}`, `/orgs/{id}/members`, `/orgs/{id}/invite`
- **documents.py:** `/docs`, `/docs/{id}`, `/docs/{id}/download`, `/docs/batch-upload`
- **ai.py:** `/ai/chat`, `/ai/summary`, `/ai/quiz`, `/ai/translate`, `/ai/extract`, `/ai/compare`
- **billing.py:** `/billing/checkout`, `/billing/portal`, `/billing/webhook`
- **sharing.py:** `/share/links`, `/share/links/{id}`, `/share/access/{token}`
- **analytics.py:** `/analytics/usage`, `/analytics/dashboard`, `/admin/stats`
- **export.py:** `/export/{job_id}/download`

### `/app/ai/` — AI Servisleri

- **provider.py:** LLM provider arayüzü (Ollama/OpenAI impl + fallback)
- **embeddings.py:** Embedding model (sentence-transformers)
- **vector_store.py:** pgvector CRUD + similarity search
- **rag.py:** RAG orchestration (query → embed → search → context → LLM)
- **guards.py:** Prompt injection detection + output moderation

### `/app/workers/` — Celery Task'ları

- **document_tasks.py:** `process_document(doc_id)` — metin çıkarma, OCR, chunk, embed
- **ai_tasks.py:** `generate_summary(doc_id, level)`, `create_quiz(doc_id)` vb.
- **email_tasks.py:** `send_verification_email(user_id)`, `send_invoice_email(sub_id)`
- **billing_tasks.py:** `reconcile_stripe_subscriptions()` — günlük job

---

## Frontend Detayları

### Feature-based Organizasyon

Her feature kendi dizininde (components, hooks, api):
```
features/
  auth/
    components/  LoginForm.tsx, RegisterForm.tsx
    hooks/       useAuth.ts, useLogin.ts
    api/         authApi.ts (TanStack Query mutations)
```

### Route Yapısı

```tsx
// routes/index.tsx
<Routes>
  <Route path="/" element={<HomePage />} />
  <Route path="/login" element={<LoginPage />} />
  <Route path="/register" element={<RegisterPage />} />
  
  <Route element={<ProtectedRoute />}>  {/* Auth gerekli */}
    <Route path="/dashboard" element={<DashboardPage />} />
    <Route path="/documents" element={<DocumentsPage />} />
    <Route path="/documents/:id" element={<DocumentDetailPage />} />
    <Route path="/chat/:docId" element={<ChatPage />} />
    <Route path="/billing" element={<BillingPage />} />
    <Route path="/settings" element={<SettingsPage />} />
  </Route>
  
  <Route path="*" element={<NotFoundPage />} />
</Routes>
```

---

## Docker Compose (Local Dev)

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: docassistant
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"  # S3 API
      - "9001:9001"  # Console
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    depends_on:
      - postgres
      - redis
      - minio
    volumes:
      - ./backend/app:/app/app  # Hot reload
    command: uvicorn app.main:app --host 0.0.0.0 --reload

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    env_file:
      - ./backend/.env
    depends_on:
      - postgres
      - redis
      - minio
    command: celery -A app.workers.celery_app worker --loglevel=info

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    volumes:
      - ./frontend/src:/app/src  # Hot reload
    command: npm run dev -- --host

volumes:
  postgres_data:
  minio_data:
```

---

## Test Organizasyonu

### Backend (pytest)
```
tests/
  conftest.py                # Fixtures: db_session, test_user, test_org
  test_auth.py              # Register, login, verify, reset
  test_organizations.py     # Org CRUD, membership, invitation
  test_documents.py         # Upload, list, delete
  test_ai_rag.py            # RAG doğruluğu
  test_billing.py           # Stripe mock testleri
  test_tenant_isolation.py  # Kritik: tenant izolasyon
  integration/
    test_upload_flow.py     # E2E: upload → process → ready
    test_payment_flow.py    # E2E: checkout → webhook → upgrade
```

### Frontend (Vitest + Playwright)
```
tests/
  components/
    LoginForm.test.tsx
    DocumentCard.test.tsx
  e2e/
    auth.spec.ts            # Playwright: register → login
    upload.spec.ts          # Playwright: upload → list
    chat.spec.ts            # Playwright: chat akışı
```

---

## Environment Variables (.env.example)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://dev:dev@localhost:5432/docassistant
PGVECTOR_ENABLED=true

# Redis
REDIS_URL=redis://localhost:6379/0

# Object Storage
S3_ENDPOINT=http://localhost:9000  # MinIO local
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=docassistant
S3_REGION=us-east-1

# Auth
JWT_SECRET=<random-32-byte-hex>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# AI
LLM_PROVIDER=ollama  # ollama | openai
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
# OPENAI_API_KEY=sk-...  # fallback (opsiyonel)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_BUSINESS=price_...

# Email
EMAIL_PROVIDER=resend  # resend | sendgrid
RESEND_API_KEY=re_...
EMAIL_FROM=noreply@docassistant.com

# Monitoring
SENTRY_DSN=https://...
POSTHOG_API_KEY=phc_...

# Features
ENABLE_2FA=true
ENABLE_MALWARE_SCAN=false  # ClamAV/VirusTotal için true
```

---

## Detaylar

Faz bazlı plan: [ROADMAP.md](ROADMAP.md)
Ana plan: [PROJECT_PLAN.md](PROJECT_PLAN.md)
