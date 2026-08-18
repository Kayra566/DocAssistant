# DocAssistant — Proje Planı

> AI destekli, çok kiracılı (multi-tenant) doküman asistanı SaaS uygulaması.
> Bu belge; kapsam, mimari, teknoloji seçimleri, veri modeli, güvenlik, test ve
> faz bazlı yol haritasını tanımlar. Ayrıca ilk istekte **olmayan ama kritik**
> maddeleri işaretler (bkz. [Bölüm 4](#4-kritik-eksikler--öneriler-yeni-eklenenler)).

---

## 1. Proje Özeti & Hedefler

| Konu | Değer |
|------|-------|
| Ürün | Dokümanları yükleyip 7 farklı AI işlemiyle (chat, özet, quiz vb.) işleyen SaaS |
| Kullanıcı tipi | Bireysel kullanıcı + ekip/organizasyon (B2B & B2C) |
| İş modeli | Abonelik (Free / Pro / Business) — Stripe |
| Çekirdek değer | RAG ile "dokümanla konuşma", sayfa referanslı güvenilir yanıtlar |
| Kalite hedefi | Güvenli, izole (tenant), ölçeklenebilir, gözlemlenebilir |

**Başarı kriterleri (ilk sürüm için):**
- Doküman yükleme → işleme → sorgulama akışı uçtan uca çalışır.
- Tenant izolasyonu her sorguda garanti altında (sızıntı = 0).
- AI maliyeti kullanıcı bazında izlenir ve kotayla sınırlanır.
- Ödeme ve abonelik yaşam döngüsü (upgrade/downgrade/cancel) sorunsuz.

---

## 2. Mimari Genel Bakış

```mermaid
flowchart TB
    subgraph Client["🎨 Frontend (React 18 + Vite + TS)"]
        UI[shadcn/ui + Tailwind]
        State[Zustand + TanStack Query]
    end

    subgraph Edge["🌐 Edge / Gateway"]
        LB[Reverse Proxy / Nginx]
        RL[Rate Limiter]
    end

    subgraph API["⚙️ FastAPI (async)"]
        Auth[Auth / JWT]
        Docs[Doküman Servisi]
        AI[AI Orkestrasyon]
        Billing[Stripe Servisi]
        Share[Paylaşım Servisi]
    end

    subgraph Workers["🔁 Celery Workers"]
        Ingest[Doküman İşleme / OCR / Chunking]
        AIJobs[Uzun AI İşleri]
        Emails[Email / Bildirim]
    end

    subgraph Data["🗄️ Veri Katmanı"]
        PG[(PostgreSQL)]
        Vec[(Vector DB\npgvector / Qdrant)]
        Redis[(Redis\ncache + queue + rate limit)]
        Obj[(Object Storage\nS3 / MinIO)]
    end

    subgraph External["🔌 Dış Servisler"]
        LLM[LLM Provider\n+ fallback]
        Stripe[Stripe]
        Mail[Resend / SendGrid]
        Sentry[Sentry / PostHog]
    end

    Client --> Edge --> API
    API --> Redis
    API --> PG
    API --> Obj
    API --> Vec
    API -- enqueue --> Redis
    Workers --> Redis
    Workers --> PG
    Workers --> Vec
    Workers --> Obj
    AI --> LLM
    Billing --> Stripe
    Emails --> Mail
    API --> Sentry
```

**Neden bu şekil?**
- Uzun AI işleri (özet, quiz, çeviri, ingest) HTTP isteğini bloklamamalı → **Celery**.
- RAG için embedding + arama ayrı bir vector store gerektirir.
- Dosyalar DB'de değil, **object storage**'da tutulmalı (imzalı URL ile erişim).

---

## 3. Teknoloji Yığını (Onaylanan)

| Katman | Teknoloji |
|--------|-----------|
| Backend | FastAPI, async SQLAlchemy 2.0, Pydantic v2 |
| DB | PostgreSQL 16 + **pgvector** (vector store), Alembic (migration) |
| RAG | LangChain + sentence-transformers (embedding) |
| LLM | **Yerel (Ollama / llama.cpp)** + opsiyonel OpenAI fallback |
| Cache/Queue | Redis, Celery |
| Object Storage | **MinIO** (local) + **S3** (production) |
| Frontend | React 18, TypeScript, Vite, Tailwind, shadcn/ui |
| FE State | Zustand, TanStack Query, React Hook Form + Zod |
| i18n | react-i18next (**TR + EN**) |
| Ödeme | Stripe |
| Email | Resend veya SendGrid |
| Gözlem | Sentry, PostHog, yapılandırılmış JSON log |
| Konteyner | Docker, docker-compose, GitHub Actions |

**Not:** Kota takibi yerel LLM için de **token/maliyet** bazlı yapılacak (self-host maliyet izleme).

---

## 4. Kritik Eksikler / Öneriler (YENİ — eklenenler)

> İlk istek listesinde **olmayan** ama production için **kritik** gördüğüm maddeler.
> Öncelik: 🔴 zorunlu · 🟡 önemli · 🟢 iyi olur.

### Altyapı & Veri
- ✅ **4.1 Object Storage:** **MinIO (local) + S3 (production)** seçildi. Dosyalar DB'de değil object storage'da, imzalı URL ile erişim.
- ✅ **4.2 LLM Provider:** **Yerel (Ollama / llama.cpp)** birincil, opsiyonel OpenAI fallback. `LLMProvider` arayüzü + timeout/retry stratejisi.
- ✅ **4.3 Vector DB:** **pgvector** seçildi (operasyon basitliği, backup/restore kolaylığı).
- ✅ **4.4 AI maliyet & token takibi:** Kota **token/maliyet** bazlı (yerel LLM için de hesaplanacak). İşlem öncesi token tahmini + tenant bazlı aylık tavan + aşımda durdurma.
- 🟡 **4.5 RAG işleme boru hattı detayı:** Chunking stratejisi, embedding modeli, sayfa/koordinat eşleme, tekrar-eden içerik (dedup), yeniden-embed (re-index) tetikleri netleştirilmeli. Sayfa referanslı yanıt buna bağlı.
- 🟡 **4.6 AI sonuç önbellekleme:** Aynı doküman + aynı istek için sonuç cache'lenerek maliyet düşürülür (Redis / DB).

### Güvenlik & Uyumluluk
- 🔴 **4.7 Stripe webhook idempotency + reconciliation:** Webhook'lar tekrar gelebilir; idempotency key + event log + periyodik durum eşitleme (reconcile) şart.
- 🔴 **4.8 Yasal sayfalar:** Kullanım Şartları (ToS), Gizlilik Politikası, Çerez onayı. GDPR ve Stripe onboarding için zorunlu.
- 🟡 **4.9 AI çıktı moderasyonu + PII maskeleme:** Prompt injection listede var; ek olarak zararlı çıktı filtreleme ve dokümandaki kişisel verinin log'a sızmaması gerekir.
- 🟡 **4.10 Email deliverability (SPF/DKIM/DMARC):** Doğrulama/şifre-sıfırlama mailleri spam'e düşmesin diye domain kimlik doğrulaması.
- 🟢 **4.11 Secrets yönetimi:** `.env` yeterli değil; production'da gizli anahtarlar için vault/secret manager.

### Ürün & Kullanıcı Deneyimi
- 🔴 **4.12 Test stratejisi:** Listede test yok. pytest (backend), Vitest + React Testing Library (FE), Playwright (E2E), yük testi (k6/Locust). CI'ya bağlanmalı.
- 🟡 **4.13 Streaming yanıt (SSE/WebSocket):** Chat cevabı token token akmalı; yoksa UX zayıf olur.
- 🟡 **4.14 Onboarding + boş durum (empty state) + landing page:** İlk kullanıcı deneyimi ve pazarlama sayfası.
- ✅ **4.15 i18n:** **TR + EN** (react-i18next). Backend hata mesajları + email şablonları da çok dilli.
- 🟢 **4.16 Erişilebilirlik (a11y):** shadcn temeli iyi; klavye/aria kontrolleri hedeflensin.
- 🟢 **4.17 PWA / mobil uyum:** Responsive + opsiyonel PWA.

### Operasyon
- 🔴 **4.18 Yedekleme & felaket kurtarma:** Postgres + vector store + object storage için otomatik yedek ve geri-yükleme testi.
- 🟡 **4.19 API versiyonlama:** `/api/v1/...` baştan.
- 🟡 **4.20 Gözlemlenebilirlik (metrics/tracing):** Sentry hata için iyi; ek olarak OpenTelemetry + Prometheus/Grafana metrikleri + uptime/health-check izleme.
- 🟡 **4.21 Staging ortamı + feature flags:** Prod öncesi test ortamı ve kademeli özellik açma.
- 🟢 **4.22 Soft delete + veri saklama politikası + audit log değişmezliği (immutability):** "Right to be forgotten" ile uyumlu saklama süreleri.
- 🟢 **4.23 Idempotency (genel):** Batch upload ve AI tetiklemede çift işlemi önlemek için idempotency key.

---

## 5. Veri Modeli (Ana Varlıklar)

```mermaid
erDiagram
    ORGANIZATION ||--o{ MEMBERSHIP : has
    USER ||--o{ MEMBERSHIP : belongs
    ORGANIZATION ||--o{ DOCUMENT : owns
    USER ||--o{ DOCUMENT : uploads
    DOCUMENT ||--o{ DOCUMENT_CHUNK : split_into
    DOCUMENT ||--o{ AI_JOB : processed_by
    DOCUMENT ||--o{ SHARE_LINK : shared_via
    DOCUMENT ||--o{ COMMENT : has
    ORGANIZATION ||--|| SUBSCRIPTION : billed_by
    ORGANIZATION ||--o{ USAGE_RECORD : tracks
    USER ||--o{ AUDIT_LOG : generates
    ORGANIZATION ||--o{ INVITATION : invites

    ORGANIZATION {
        uuid id PK
        string name
        string plan
        timestamp created_at
    }
    USER {
        uuid id PK
        string email
        string password_hash
        bool is_verified
        bool totp_enabled
    }
    MEMBERSHIP {
        uuid id PK
        uuid user_id FK
        uuid org_id FK
        string role "owner|admin|member|viewer"
    }
    DOCUMENT {
        uuid id PK
        uuid org_id FK
        uuid owner_id FK
        string filename
        string storage_key
        string mime_type
        int size_bytes
        string status "uploaded|processing|ready|failed"
        bool is_favorite
        timestamp created_at
    }
    AI_JOB {
        uuid id PK
        uuid document_id FK
        string type "chat|summary|keypoints|quiz|translate|extract|compare"
        string status
        jsonb params
        jsonb result
        int tokens_used
        numeric cost
    }
    SUBSCRIPTION {
        uuid id PK
        uuid org_id FK
        string stripe_customer_id
        string stripe_sub_id
        string plan
        string status
        timestamp current_period_end
    }
    USAGE_RECORD {
        uuid id PK
        uuid org_id FK
        string metric "ai_tokens|documents|storage"
        numeric value
        date period
    }
```

**Tenant izolasyonu kuralı:** Her sorguda `org_id` (ve gerektiğinde `user_id`)
filtresi zorunlu. Bunu tek noktadan garanti etmek için repository katmanında
**otomatik tenant scoping** (SQLAlchemy event / dependency) kullanılacak.

---

## 6. Modül Bazlı Kapsam

| # | Modül | Kapsam özeti |
|---|-------|--------------|
| M1 | Auth & Kullanıcı | Register/login, JWT + refresh rotation, email doğrulama, şifre sıfırlama, 2FA (TOTP/Pro), zxcvbn, account lockout |
| M2 | Multi-tenant | Organization/Workspace, 4 rol, davet/yönetim, tenant scoping |
| M3 | Doküman Yönetimi | Yükleme (PDF/DOCX/XLSX/PPTX/TXT/MD/resim-OCR), magic-bytes doğrulama, boyut limiti, batch upload, liste/sil/favori, object storage |
| M4 | İşleme Boru Hattı | Metin çıkarma, OCR, chunking, embedding, vector index, sayfa eşleme (Celery) |
| M5 | AI Özellikleri | Chat (RAG), Summary (4 seviye), Key Points, Quiz, Translation, Data Extraction, Compare |
| M6 | Ödeme | Stripe 3 plan, upgrade/downgrade/cancel, webhook, kota/tier |
| M7 | Dashboard & Analytics | Kullanım grafikleri (Recharts), kota takibi, admin panel |
| M8 | Paylaşım & İşbirliği | Shareable links, ekip paylaşımı, history, yorum/not |
| M9 | Export & Templates | PDF/DOCX/XLSX/MD export, prompt şablonları (hukuk/akademik/iş) |
| M10 | Güvenlik | Rate limit, XSS/CSRF/SQLi, prompt injection, malware scan, signed URL, audit log, GDPR, AES-256 at-rest |
| M11 | Bildirim | Transactional email, in-app notification |
| M12 | DevOps & Gözlem | Docker, CI/CD, Sentry, PostHog, JSON log, health check, backup |
| M13 | Dokümantasyon | Swagger/OpenAPI, mimari diyagramlar, README, `.env.example` |

---

## 7. Geliştirme Yol Haritası

**Detaylı faz planı:** [ROADMAP.md](ROADMAP.md)

**Özet:**
- **Faz 0:** Temel & İskele (Docker, CI, test, API versiyonlama)
- **Faz 1:** Auth & Multi-tenant
- **Faz 2:** Doküman yönetimi + işleme (MinIO, pgvector)
- **Faz 3:** RAG chat (yerel LLM, streaming)
- **Faz 4:** Diğer AI özellikleri (summary, quiz vb.)
- **Faz 5:** Ödeme & kota (Stripe)
- **Faz 6:** Dashboard, paylaşım, export
- **Faz 7:** Sertleştirme, güvenlik, i18n (TR+EN), yayın

**Süre:** ~12-16 hafta (tam zamanlı 1-2 geliştirici).

---

## 8. Güvenlik & Uyumluluk Kontrol Listesi

- [ ] Tüm sorgularda tenant scoping (otomatik + testli)
- [ ] Endpoint bazlı rate limiting (Redis)
- [ ] Girdi doğrulama (Pydantic) + çıktı encode (XSS)
- [ ] CSRF koruması (cookie tabanlı akış için)
- [ ] Parametreli sorgular (SQLi) — ORM zorunlu
- [ ] Prompt injection guard + AI çıktı moderasyonu
- [ ] Dosya magic-bytes + boyut + malware scan
- [ ] Signed URL (kısa ömürlü) ile indirme
- [ ] Audit log (kim/ne/ne zaman) — değişmez
- [ ] AES-256 at-rest (dosya + hassas alanlar), TLS in-transit
- [ ] GDPR: veri dışa aktarma + "unutulma hakkı"
- [ ] Secrets vault / güvenli env yönetimi

---

## 9. Test Stratejisi

| Seviye | Araç | Kapsam |
|--------|------|--------|
| Unit | pytest, Vitest | Servis/util/hook mantığı |
| Integration | pytest + testcontainers | DB, Redis, storage, Stripe mock |
| Contract | schemathesis | OpenAPI şema uyumu |
| E2E | Playwright | Kritik kullanıcı akışları |
| Yük | k6 / Locust | Yükleme + AI eşzamanlılığı |
| Güvenlik | Bandit, npm audit, ZAP | Statik + dinamik tarama |

Hedef: kritik yollarda anlamlı kapsama + CI'da zorunlu geçiş.

---

## 10. Ortamlar & DevOps

- **local:** docker-compose (tüm bağımlılıklar dahil)
- **staging:** prod'a yakın, gerçek Stripe test modu
- **production:** yönetilen Postgres + Redis + S3 + konteyner orkestrasyonu
- CI/CD: GitHub Actions (lint → test → build → image → deploy)
- Gözlem: Sentry (hata), PostHog (ürün analitiği), Prometheus/Grafana (metrik), health checks

---

## 11. Önerilen Klasör Yapısı

```
DocAssistant/
├── backend/
│   ├── app/
│   │   ├── api/v1/            # router'lar
│   │   ├── core/             # config, security, logging
│   │   ├── models/           # SQLAlchemy
│   │   ├── schemas/          # Pydantic
│   │   ├── services/         # iş mantığı
│   │   ├── ai/               # provider soyutlama, RAG, prompt'lar
│   │   ├── workers/          # Celery task'ları
│   │   └── repositories/     # tenant-scoped erişim
│   ├── alembic/
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/ (ui/)
│   │   ├── features/
│   │   ├── hooks/  lib/  stores/
│   │   └── routes/
│   └── tests/
├── infra/
│   ├── docker/               # Dockerfile'lar (multi-stage)
│   └── docker-compose.yml
├── docs/
└── .github/workflows/
```

---

## 12. Başlıca Riskler

| Risk | Etki | Azaltma |
|------|------|---------|
| AI maProje Klasör Yapısı

**Detaylı yapı:** [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

```
DocAssistant/
├── backend/      # FastAPI, SQLAlchemy, Celery, AI servisleri
├── frontend/     # React + Vite, shadcn/ui, TanStack Query
├── infra/        # Docker, docker-compose, K8s (opsiyonel)
├── docs/         # PROJECT_PLAN, ROADMAP, STRUCTURE, API
└── .github/workflows/  # CI/CDyerel LLM için bile) |
| Tenant veri sızıntısı | Kritik | Otomatik scoping + izolasyon testleri |
| Yerel LLM kesintisi | Orta | OpenAI fallback + retry/timeout |
| Uzun AI işlerinde timeout | Orta | Celery + streaming + iş durumu takibi |
| Stripe webhook tutarsızlığı | Yüksek | Idempotency + reconciliation |
| MinIO/S3 erişim hatası | Orta | Signed URL retry + health check✅ Onaylanmış Kararlar

1. **LLM sağlayıcı:** Yerel (Ollama / llama.cpp) birincil, opsiyonel OpenAI fallback
2. **Vector DB:** pgvector (operasyon basitliği)
3. **Object storage:** MinIO (local) + S3 (production)
4. **i18n:** TR + EN (react-i18next)
5. **Kota birimi:** Token/maliyet (yerel LLM için de hesaplanacak)

> ✅ Kararlar alındı, Faz 0 iskelesine başlanabilir.

---

## 14. İlgili Belgeler

- **Faz bazlı yol haritası:** [ROADMAP.md](ROADMAP.md)
- **Detaylı klasör yapısı:** [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
- **Mimari diyagramlar:** [ARCHITECTURE.md](ARCHITECTURE.md) *(Faz 0'da oluşturulacak)*
- **Güvenlik politikaları:** [SECURITY.md](SECURITY.md) *(Faz 7'de oluşturulacak)*