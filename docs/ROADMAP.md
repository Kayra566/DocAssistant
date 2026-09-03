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
- [x] Veri modeli: `Document`, `DocumentChunk` (metadata: page, bbox)
- [x] Upload endpoint + magic-bytes doğrulama + boyut limiti
- [x] Batch upload (toplu)
- [ ] Malware scan (ClamAV / VirusTotal API) — Faz 7'ye ertelendi
- [x] Liste/sil/favori API'ları
- [x] Signed URL oluşturma (indirme için, 1 saat TTL)
- [x] Celery worker kurulumu (eager mod + task)
- [x] İşleme pipeline (task):
  - PDF/DOCX/XLSX/PPTX/TXT/MD → metin çıkarma (pypdf/python-docx/openpyxl/python-pptx)
  - Resim → OCR (Tesseract, opsiyonel/feature-flag)
  - Chunking (örtüşmeli, sayfa eşlemeli)
  - Embedding (hashing embedder; sentence-transformers'a geçiş açık)
  - Vektör kaydı (JSON embedding; pgvector'a geçiş yolu açık)
- [x] Doküman durumu izleme: `uploaded` → `processing` → `ready` / `failed`
- [x] Frontend: drag-drop yükleme (react-dropzone)
- [x] Frontend: doküman listesi
- [x] Test: upload → işleme → chunk → indirme (E2E)

### Teslim Kriteri
- PDF yüklenir, otomatik işlenir, "ready" olur.
- pgvector'de chunk'lar + embedding'ler sorgulanabilir.
- İşlem hatası olursa durum "failed" + hata logu.

---

## Faz 3 — AI Çekirdeği: RAG Chat (M5 kısmi)

**Hedef:** Dokümanla soru-cevap, sayfa referanslı yanıt, streaming.

### Görevler
- [x] LLM provider soyutlama (yerel: Ollama HTTP API + fake sağlayıcı)
  - Retry/timeout + fallback (OpenAI API yedek olarak opsiyonel)
- [x] RAG servisi:
  - Soru → embedding → similarity search
  - Chunk'ları context'e ekle + prompt template
  - LLM → yanıt + sayfa referansları (metadata'dan)
- [x] Streaming (SSE) — token token cevap akışı
- [x] Prompt injection guard (input validation + prompt template güvenliği)
- [x] AI çıktı moderasyonu (basit hook — Faz 7'de genişleyecek)
- [x] Token/maliyet takibi:
  - Token sayma (kaba tahmin; gerçek tokenizer'a geçiş açık)
  - Tahmini maliyet (yerel için 0)
  - Kota kontrolü: tenant bazlı aylık token limiti
- [x] AI sonuç önbellekleme (`doc_id + query hash → result`; memory/redis)
- [x] Veri modeli: `AIJob` (type=chat, status, tokens_used, cost) + Conversation/ChatMessage
- [x] Frontend: chat UI (mesaj listesi + input + citations)
- [ ] Frontend: sayfa referansları tıklanınca PDF viewer'da o sayfa — Faz 6'ya ertelendi
- [x] Test: RAG doğruluğu (fixture doküman + soru → citations)

### Teslim Kriteri
- Kullanıcı PDF yükler, "Bu dokümanda ne yazıyor?" sorar.
- Sistem doğru chunk'u bulur, LLM ile yanıt verir, sayfa numarası gösterir.
- Aynı soru tekrar sorulunca cache'den döner.

---

## Faz 4 — Diğer AI Özellikleri (M5 kalan)

**Hedef:** Summary, Key Points, Quiz, Translation, Data Extraction, Compare.

### Görevler
- [x] **Summary:** 4 seviye (kısa/detaylı/madde/executive) — LLM prompt'ları
- [x] **Key Points:** Tarih, isim, sayı, karar çıkarma (JSON çıktı)
- [x] **Quiz:** Test/doğru-yanlış/açık-uçlu sorular üret (JSON çıktı)
- [x] **Translation:** Kaynak dil → hedef dil (Markdown formatı koru)
- [x] **Data Extraction:** Tablo/liste → JSON (yapılandırılmış çıktı)
  - Excel export → Faz 6'ya (M9 Export) ertelendi
- [x] **Compare:** İki doküman → diff analizi (only_in_a / only_in_b / changed)
- [x] Prompt şablonları (M9): hukuk/akademik/iş — preset'ler
- [x] Her özellik için:
  - Celery task (`ai.run_job`; `AI_JOBS_EAGER=false` ile async)
  - Token takibi + kota + sonuç önbelleği
  - `AIJob.params` / `AIJob.result` ile kalıcılık + geçmiş erişimi
  - Frontend: özel UI (Quiz → soru kartları, Extract → tablo, Compare → diff)
- [x] Test: her özellik için en az 1 E2E test

### Teslim Kriteri
- Tüm 7 AI özelliği çalışır, sonuçlar kaydedilir, kullanıcı tekrar erişebilir.

---

## Faz 5 — Ödeme & Kota (M6)

**Hedef:** Stripe abonelik + tier bazlı kota sistemi.

### Görevler
- [x] Stripe entegrasyonu (test modu) + `fake` sağlayıcı (dev/test için)
- [x] Veri modeli: `Subscription`, `UsageRecord`, `WebhookEvent`
- [x] 3 plan tanımı:
  - **Free:** 10 doküman, 100 AI istek/ay, 50 MB depolama
  - **Pro:** 100 doküman, 1000 AI istek/ay, 1 GB, 2FA
  - **Business:** sınırsız doküman, 10000 AI istek/ay, 10 GB, öncelikli destek
- [x] Checkout session + redirect
- [x] Customer portal (plan değiştir, iptal et)
- [x] Webhook endpoint + idempotency (`webhook_events` event log tablosu)
- [x] Reconciliation job (günlük Stripe durumu senkronize et — Celery beat)
- [x] Kota zorlama:
  - Doküman/depolama ve AI istek/token kontrolü işlem öncesi
  - Aşımda HTTP 402 Payment Required + mesaj
- [x] Usage tracking (aylık reset — `period_start` bazlı sayaçlar)
- [x] Frontend: fiyatlandırma sayfası + upgrade flow + kota progress bar
- [x] Test: webhook mock, idempotency, kota aşımı, reconciliation senaryoları

### Teslim Kriteri
- Kullanıcı Free planla başlar, 10. dokümanda bloke olur.
- Pro'ya upgrade yapar, Stripe ödeme aldığında sistem planı günceller.
- Abonelik iptal edilirse bir sonraki dönem sonu planı Free'ye düşer.

---

## Faz 6 — Dashboard, Paylaşım, Export (M7, M8, M9)

**Hedef:** Kullanıcı deneyimi tamamlama, işbirliği özellikleri.

### Görevler
- [x] **Dashboard (M7):**
  - Recharts grafikleri (kullanım trendi, AI işlem dağılımı)
  - Kota progress bar
  - Admin panel (platform yönetimi — superuser rolü)
- [x] **Paylaşım (M8):**
  - Veri modeli: `ShareLink` (token, expiry, permissions)
  - Shareable link oluşturma (public/email-specific)
  - Ekip içi doküman paylaşımı (rol bazlı izin)
  - History: işlem log'u (kim ne zaman ne yaptı)
  - Yorum/not sistemi (`DocumentComment`)
- [x] **Export (M9):**
  - AI sonuçlarını PDF/DOCX/XLSX/MD olarak indir
  - Export API + arka plan işi (Celery)
- [x] Frontend: dashboard sayfası, paylaşım modal, export butonu
- [x] Test: share link erişim kontrolü, export format doğruluğu

### Teslim Kriteri
- Kullanıcı dashboard'unda kullanımını görür.
- Dokümanı link ile paylaşır, alıcı izinli şekilde erişir.
- AI sonucunu DOCX olarak indirir.

---

## Faz 7 — Sertleştirme & Yayına Hazırlık (M10, M11, M12, M13)

**Hedef:** Production-ready, güvenli, gözlemlenebilir, dokümante sistem.

### Görevler

#### Güvenlik (M10)
- [x] Güvenlik denetimi:
  - Bandit (Python), npm audit (Node.js) — CI'da ayrı job
  - [ ] OWASP ZAP taraması — çalışan staging URL'i gerektirir
- [x] GDPR uyumluluğu:
  - Veri export API (`GET /api/v1/gdpr/export`)
  - Right to be forgotten (`POST /api/v1/gdpr/delete-account`)
  - Privacy policy, ToS, Cookie consent sayfaları
- [x] Audit log değişmezliği (HMAC hash zinciri + Postgres append-only trigger)
- [x] Encryption at rest (AES-256-GCM — TOTP sırları)
- [x] Rate limiting (IP/kullanıcı bazlı, auth uçları için sıkı limit, redis backend)
- [x] PII maskeleme (log filtresi: e-posta, token, JWT, kart)
- [x] Güvenlik başlıkları (CSP, HSTS, X-Frame-Options, Referrer-Policy)

#### Bildirimler (M11)
- [x] Email provider soyutlaması (console / Resend / SendGrid)
- [x] Transactional email şablonları:
  - Email verification, password reset, ekip daveti, ödeme hatası, kota uyarısı
- [x] SPF/DKIM/DMARC domain authentication — DNS adımları DEPLOYMENT.md'de
- [x] In-app notification sistemi (navbar rozeti + okundu işaretleme)
- [ ] Test: email deliverability — gerçek domain ve sağlayıcı hesabı gerektirir

#### DevOps & Gözlem (M12)
- [x] Multi-stage Docker build (runtime-only bağımlılık, non-root user, healthcheck)
- [x] CI/CD pipeline:
  - Test coverage raporu (artifact olarak yüklenir)
  - Security scan (bandit + npm audit), yüksek şiddette fail
  - E2E job (Playwright)
  - [ ] Image registry push + staging/production deploy — registry ve ortam kimlik bilgisi gerektirir
- [x] Sentry kurulumu (backend + frontend, DSN yoksa devre dışı)
- [x] PostHog kurulumu (yalnızca çerez onayı verildiyse başlar)
- [x] Prometheus metrikleri (`/metrics`: istek sayısı, latency, DB pool)
- [x] Health check endpoint (`/health` liveness, `/api/v1/ready` DB+Redis)
- [x] Yedekleme stratejisi:
  - `infra/scripts/backup.sh` (pg_dump + S3 + retention)
  - `infra/scripts/restore.sh` (doğrulamalı geri yükleme)
  - [ ] Backup restore testi — staging Postgres örneği gerektirir
- [ ] Secrets vault (AWS Secrets Manager / Vault) — akış DEPLOYMENT.md'de, bağlanması bulut hesabı gerektirir
- [x] Staging ortamı setup (`infra/docker-compose.staging.yml`)
- [x] Feature flags (config tabanlı, `GET /api/v1/features`)

#### Dokümantasyon & Onboarding (M13)
- [x] Swagger/OpenAPI tamamlama (açıklama + tag metadata)
- [x] README: kurulum ve katkı rehberi
- [x] DEPLOYMENT.md (production kurulum adımları)
- [x] TROUBLESHOOTING.md (sık sorunlar)
- [x] `.env.example` — tüm değişkenler açıklamalı (backend + frontend)
- [x] i18n (TR/EN):
  - Backend: hata mesajları (Accept-Language) + email şablonları
  - Frontend: react-i18next + dil seçici
- [x] Onboarding flow (ilk giriş kontrol listesi, feature-flag'li)
- [x] Landing page (pazarlama sayfası)
- [x] Erişilebilirlik (a11y): ARIA etiketleri, klavye odağı, focus-visible halkaları
- [ ] Mimari diyagramları güncelle (deployment, sequence)

#### Test & Yük
- [x] E2E test coverage: kritik kullanıcı yolları (Playwright)
- [x] Yük testi scriptleri (k6):
  - Doküman yükleme (100 eşzamanlı) — `infra/loadtest/upload.js`
  - AI chat (50 eşzamanlı) + vektör arama — `infra/loadtest/chat.js`
- [ ] Sonuçlara göre optimizasyon — yük testi production benzeri ortamda koştuktan sonra

### Teslim Kriteri
- [x] Güvenlik taraması temiz (bandit + npm audit CI'da, kritik bulgu yok).
- [x] Dokümantasyon eksiksiz (DEPLOYMENT, TROUBLESHOOTING, .env.example, OpenAPI).
- [x] Yedekleme ve geri yükleme scriptleri hazır.
- [x] Yük testi senaryoları hazır.
- [x] Production deployment checklist hazır (DEPLOYMENT.md §12).
- [ ] Staging'de production benzeri ortamda tüm akışlar test edilmiş — gerçek staging altyapısı gerektirir.

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
