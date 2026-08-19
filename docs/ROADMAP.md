# DocAssistant — Geliştirme Yol Haritası

> Bu belge projenin faz bazlı geliştirme planını tanımlar.
> Her faz kendi içinde çalışır bir dilim (vertical slice) üretir ve sonda demo edilebilir.

---

## Faz Özeti

| Faz | Süre (tahmini) | Modüller | Çıktı |
|-----|----------------|----------|-------|
| 0 | 3-5 gün | Temel & İskele | Boilerplate + CI + Docker + test iskeleti |
| 1 | 1-2 hafta | M1, M2 | Auth + Multi-tenant çalışır |
| 2 | 2-3 hafta | M3, M4 | Doküman yükleme + işleme + embedding |
| 3 | 2-3 hafta | M5 (kısmi) | RAG chat (sayfa referanslı) |
| 4 | 2-3 hafta | M5 (kalan) | 6 AI özelliği daha (summary, quiz vb.) |
| 5 | 1-2 hafta | M6 | Ödeme + kota sistemi |
| 6 | 1-2 hafta | M7, M8, M9 | Dashboard + paylaşım + export |
| 7 | 2-3 hafta | M10, M11, M12, M13 | Sertleştirme + güvenlik + dokümantasyon + yayın |

**Toplam:** ~12-16 hafta (3-4 ay) — tam zamanlı 1-2 geliştirici için.

---

## Faz 0 — Temel & İskele

**Hedef:** Proje temeli, tüm ekip aynı ortamda çalışabilir.

### Görevler
- [X] Monorepo yapısı kur (`backend/`, `frontend/`, `infra/`, `docs/`)
- [x] `docker-compose.yml` — Postgres, Redis, MinIO, backend, frontend, worker
- [x] Backend: FastAPI iskelet + async SQLAlchemy + Alembic
- [x] Frontend: Vite + React 18 + TypeScript + Tailwind + shadcn/ui
- [x] `.env.example` — tüm değişkenler açıklamalı
- [x] pre-commit hooks (black, ruff, prettier, eslint)
- [x] CI: GitHub Actions (lint + test çalıştır)
- [x] Test iskeleti: pytest, Vitest
- [x] API versiyonlama (`/api/v1/`)
- [x] README: kurulum, çalıştırma, katkı rehberi
- [x] Dokümantasyon: `docs/` klasörü yapısı

### Teslim Kriteri
```bash
docker-compose up
# → Backend http://localhost:8000/docs (Swagger)
# → Frontend http://localhost:5173
```

---

## Faz 1 — Auth & Multi-tenant (M1, M2)

**Hedef:** Kullanıcı sistemi + organizasyon/ekip yönetimi.

### Görevler
- [x] Veri modeli: `User`, `Organization`, `Membership`, `Invitation`
- [x] Register + email doğrulama (verification token)
- [x] Login → JWT (access + refresh) + rotation
- [x] Şifre sıfırlama (reset token)
- [x] Password strength (zxcvbn) + account lockout (5 hata)
- [x] 2FA (TOTP) — Pro planla feature-flag'li
- [x] Organizasyon oluşturma + güncelleme
- [x] Ekip daveti + rol yönetimi (Owner/Admin/Member/Viewer)
- [x] Tenant scoping altyapısı (repository katmanı + otomatik filter)
- [x] RBAC middleware (endpoint bazlı rol kontrolü)
- [x] Frontend: login/register/verify/reset ekranları
- [x] Frontend: org ayarları + ekip yönetimi sayfası
- [x] Unit test: auth servisi, tenant scoping
- [x] Integration test: register → verify → login akışı

### Teslim Kriteri
- Kullanıcı register olabilir, email doğrular, giriş yapar.
- Organizasyon oluşturur, ekip davet eder, roller çalışır.
- Tenant izolasyonu test edilmiş (User A, User B'nin verisini göremiyor).

---

## Faz 2 — Doküman Yönetimi & İşleme (M3, M4)

**Hedef:** Doküman yükleme → metin çıkarma → chunking → embedding → vector index.

### Görevler
- [ ] MinIO entegrasyonu (local) + S3 adapter (prod)
- [ ] Veri modeli: `Document`, `DocumentChunk` (metadata: page, bbox)
- [ ] Upload endpoint + magic-bytes doğrulama + boyut limiti
- [ ] Batch upload (toplu)
- [ ] Malware scan (ClamAV / VirusTotal API)
- [ ] Liste/sil/favori API'ları
- [ ] Signed URL oluşturma (indirme için, 1 saat TTL)
- [ ] Celery worker kurulumu
- [ ] İşleme pipeline (task):
  - PDF/DOCX/XLSX/PPTX/TXT/MD → metin çıkarma (PyPDF2/python-docx/openpyxl)
  - Resim → OCR (Tesseract / Azure OCR)
  - Chunking (LangChain RecursiveCharacterTextSplitter, sayfa eşlemeli)
  - Embedding (yerel model: sentence-transformers/all-MiniLM-L6-v2)
  - pgvector → kayıt (sayfa + chunk metadatası)
- [ ] Doküman durumu izleme: `uploaded` → `processing` → `ready` / `failed`
- [ ] Frontend: drag-drop yükleme (react-dropzone), progress bar
- [ ] Frontend: doküman listesi (tablo + arama + filter)
- [ ] Test: upload → işleme → vector store → sorgulama (E2E)

### Teslim Kriteri
- PDF yüklenir, otomatik işlenir, "ready" olur.
- pgvector'de chunk'lar + embedding'ler sorgulanabilir.
- İşlem hatası olursa durum "failed" + hata logu.

---

## Faz 3 — AI Çekirdeği: RAG Chat (M5 kısmi)

**Hedef:** Dokümanla soru-cevap, sayfa referanslı yanıt, streaming.

### Görevler
- [ ] LLM provider soyutlama (yerel: Ollama veya llama.cpp HTTP API)
  - Retry/timeout + fallback (OpenAI API yedek olarak opsiyonel)
- [ ] RAG servisi:
  - Soru → embedding → pgvector similarity search
  - Chunk'ları context'e ekle + prompt template
  - LLM → yanıt + sayfa referansları (metadata'dan)
- [ ] Streaming (SSE) — token token cevap akışı
- [ ] Prompt injection guard (input validation + prompt template güvenliği)
- [ ] AI çıktı moderasyonu (zararlı içerik filtresi - basit regex başlangıç)
- [ ] Token/maliyet takibi:
  - Yerel LLM için token sayma (tiktoken / model tokenizer)
  - Tahmini maliyet (opsiyonel — kendi maliyetiniz yoksa sıfır)
  - Kota kontrolü: tenant bazlı aylık token limiti
- [ ] AI sonuç önbellekleme (Redis: `doc_id + query hash → result`, 1 gün TTL)
- [ ] Veri modeli: `AIJob` (type=chat, status, tokens_used, cost)
- [ ] Frontend: chat UI (mesaj listesi + input + streaming yanıt)
- [ ] Frontend: sayfa referansları tıklanınca PDF viewer'da o sayfa
- [ ] Test: RAG doğruluğu (fixture doküman + soru → beklenen yanıt)

### Teslim Kriteri
- Kullanıcı PDF yükler, "Bu dokümanda ne yazıyor?" sorar.
- Sistem doğru chunk'u bulur, LLM ile yanıt verir, sayfa numarası gösterir.
- Aynı soru tekrar sorulunca cache'den döner.

---

## Faz 4 — Diğer AI Özellikleri (M5 kalan)

**Hedef:** Summary, Key Points, Quiz, Translation, Data Extraction, Compare.

### Görevler
- [ ] **Summary:** 4 seviye (kısa/detaylı/madde/executive) — LLM prompt'ları
- [ ] **Key Points:** Tarih, isim, sayı, karar çıkarma (NER + LLM)
- [ ] **Quiz:** Test/doğru-yanlış/açık-uçlu sorular üret (JSON çıktı)
- [ ] **Translation:** Kaynak dil → hedef dil (Markdown formatı koru)
- [ ] **Data Extraction:** Tablo/liste → JSON/Excel (yapılandırılmış çıktı)
- [ ] **Compare:** İki doküman → diff analizi (semantic diff)
- [ ] Prompt şablonları (M9): hukuk/akademik/iş — preset'ler
- [ ] Her özellik için:
  - Celery task (uzun işlemler async)
  - Token takibi + cache
  - Frontend: özel UI (örn. Quiz → soru kartları)
- [ ] Test: her özellik için en az 1 E2E test

### Teslim Kriteri
- Tüm 7 AI özelliği çalışır, sonuçlar kaydedilir, kullanıcı tekrar erişebilir.

---

## Faz 5 — Ödeme & Kota (M6)

**Hedef:** Stripe abonelik + tier bazlı kota sistemi.

### Görevler
- [ ] Stripe entegrasyonu (test modu)
- [ ] Veri modeli: `Subscription`, `UsageRecord`
- [ ] 3 plan tanımı:
  - **Free:** 10 doküman, 100 AI istek/ay, 50 MB depolama
  - **Pro:** 100 doküman, 1000 AI istek/ay, 1 GB, 2FA
  - **Business:** sınırsız doküman, 10000 AI istek/ay, 10 GB, öncelikli destek
- [ ] Checkout session + redirect
- [ ] Customer portal (plan değiştir, iptal et)
- [ ] Webhook endpoint + idempotency (event log tablosu)
- [ ] Reconciliation job (günlük Stripe durumu senkronize et)
- [ ] Kota zorlama:
  - Doküman yükleme/AI istek öncesi kontrol
  - Aşımda HTTP 402 Payment Required + mesaj
- [ ] Usage tracking (aylık reset)
- [ ] Frontend: fiyatlandırma sayfası + upgrade flow
- [ ] Test: webhook mock, kota aşımı senaryosu

### Teslim Kriteri
- Kullanıcı Free planla başlar, 10. dokümanda bloke olur.
- Pro'ya upgrade yapar, Stripe ödeme aldığında sistem planı günceller.
- Abonelik iptal edilirse bir sonraki dönem sonu planı Free'ye düşer.

---

## Faz 6 — Dashboard, Paylaşım, Export (M7, M8, M9)

**Hedef:** Kullanıcı deneyimi tamamlama, işbirliği özellikleri.

### Görevler
- [ ] **Dashboard (M7):**
  - Recharts grafikleri (kullanım trendi, AI işlem dağılımı)
  - Kota progress bar
  - Admin panel (platform yönetimi — superuser rolü)
- [ ] **Paylaşım (M8):**
  - Veri modeli: `ShareLink` (token, expiry, permissions)
  - Shareable link oluşturma (public/email-specific)
  - Ekip içi doküman paylaşımı (rol bazlı izin)
  - History: işlem log'u (kim ne zaman ne yaptı)
  - Yorum/not sistemi (M8 opsiyonel — zaman varsa)
- [ ] **Export (M9):**
  - AI sonuçlarını PDF/DOCX/XLSX/MD olarak indir
  - Export API + arka plan işi (Celery)
- [ ] Frontend: dashboard sayfası, paylaşım modal, export butonu
- [ ] Test: share link erişim kontrolü, export format doğruluğu

### Teslim Kriteri
- Kullanıcı dashboard'unda kullanımını görür.
- Dokümanı link ile paylaşır, alıcı izinli şekilde erişir.
- AI sonucunu DOCX olarak indirir.

---

## Faz 7 — Sertleştirme & Yayına Hazırlık (M10, M11, M12, M13)

**Hedef:** Production-ready, güvenli, gözlemlenebilir, dokümante sistem.

### Görevler

#### Güvenlik (M10)
- [ ] Güvenlik denetimi:
  - OWASP ZAP taraması
  - Bandit (Python), npm audit (Node.js)
- [ ] GDPR uyumluluk:
  - Veri export API (kullanıcı tüm verisini indirebilir)
  - Right to be forgotten (hesap + tüm verilerini sil)
  - Privacy policy, ToS, Cookie consent sayfaları
- [ ] Audit log değişmezliği (append-only, imza)
- [ ] Encryption at rest (AES-256 — hassas alanlar)
- [ ] Rate limiting fine-tuning
- [ ] PII maskeleme (log'larda kişisel veri yok)

#### Bildirimler (M11)
- [ ] Email provider seçimi (Resend veya SendGrid)
- [ ] Transactional email şablonları:
  - Email verification, password reset, invoice, ekip daveti
- [ ] SPF/DKIM/DMARC domain authentication
- [ ] In-app notification sistemi (basit — navbar badge)
- [ ] Test: email deliverability (staging'de gerçek mail gönder)

#### DevOps & Gözlem (M12)
- [ ] Multi-stage Docker build (prod image'ı optimize)
- [ ] CI/CD pipeline tamamla:
  - Test coverage raporu (80%+ hedef)
  - Security scan + fail on high severity
  - Image registry push
  - Staging deploy (otomatik)
  - Production deploy (manuel onay)
- [ ] Sentry kurulumu (backend + frontend)
- [ ] PostHog kurulumu (product analytics)
- [ ] Prometheus/Grafana metrikleri (API latency, DB pool, cache hit rate)
- [ ] Health check endpoint (`/health`, `/ready`)
- [ ] Yedekleme stratejisi:
  - Postgres: pg_dump günlük, S3'e yükle
  - pgvector: aynı Postgres backup'ına dahil
  - Object storage: versioning açık
  - Backup restore testi (staging'de)
- [ ] Secrets vault (AWS Secrets Manager / HashiCorp Vault)
- [ ] Staging ortamı setup
- [ ] Feature flags (LaunchDarkly / custom)

#### Dokümantasyon & Onboarding (M13)
- [ ] Swagger/OpenAPI tamamlama (tüm endpoint'ler açıklamalı)
- [ ] Mimari diyagramlar güncelle (Mermaid — deployment, sequence)
- [ ] README: katkı rehberi, kod stili, PR süreci
- [ ] DEPLOYMENT.md (production kurulum adımları)
- [ ] TROUBLESHOOTING.md (sık sorunlar)
- [ ] `.env.example` — tüm değişkenler açıklamalı
- [ ] i18n (TR/EN):
  - Backend: hata mesajları + email şablonları
  - Frontend: react-i18next + çeviri dosyaları
- [ ] Onboarding flow (ilk giriş: walkthrough, örnek doküman yükle)
- [ ] Landing page (pazarlama sayfası)
- [ ] Erişilebilirlik (a11y): klavye navigasyonu + ARIA + contrast

#### Test & Yük
- [ ] E2E test coverage: kritik kullanıcı yolları (Playwright)
- [ ] Yük testi (k6 / Locust):
  - Doküman yükleme (100 eşzamanlı)
  - AI chat (50 eşzamanlı)
  - Vektör arama performansı
- [ ] Sonuçlara göre optimizasyon (DB index, cache, query tuning)

### Teslim Kriteri
- Staging'de production benzeri ortamda tüm akışlar test edilmiş.
- Güvenlik taraması temiz (kritik zafiyet yok).
- Dokümantasyon eksiksiz.
- Yedekleme ve restore test edilmiş.
- Yük testi hedefleri karşılanmış.
- Production deployment checklist hazır.

---

## Faz Sonrası: Production'a Geçiş

- [ ] Domain + SSL sertifikası
- [ ] Production ortamı provision (DB, Redis, S3, container hosting)
- [ ] Environment variable'ları secrets vault'a taşı
- [ ] Stripe production mode'a geç + webhook URL güncelle
- [ ] Email gönderim domain doğrulama
- [ ] Monitoring alarm'ları kur (uptime, error rate, disk kullanımı)
- [ ] Beta test grubu davet et
- [ ] Soft launch (feature flag ile kademeli açma)
- [ ] Public launch 🚀

---

## Detaylar

Proje yapısı: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
Ana plan: [PROJECT_PLAN.md](PROJECT_PLAN.md)
