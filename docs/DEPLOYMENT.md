# Deployment

Bu belge DocAssistant'ı staging ve production ortamına kurma adımlarını tanımlar.

## 1. Gereksinimler

| Bileşen | Sürüm | Not |
|---------|-------|-----|
| Docker Engine | 24+ | Compose v2 dahil |
| PostgreSQL | 16 + pgvector | Yönetilen servis önerilir |
| Redis | 7+ | Cache, Celery broker, rate limit sayacı |
| S3 uyumlu depolama | — | MinIO veya AWS S3, versioning açık |

## 2. Ortam değişkenleri

`backend/.env.example` tüm değişkenleri açıklamalarıyla listeler. Production'da
**mutlaka** değiştirilmesi gerekenler:

```bash
ENVIRONMENT=production
DEBUG=false
EXPOSE_DEV_TOKENS=false          # dev token'ları API yanıtında dönmesin
JWT_SECRET=<32+ bayt rastgele>
ENCRYPTION_KEY=<32+ bayt rastgele>   # 2FA sırlarının AES anahtarı
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
STORAGE_BACKEND=s3
RATE_LIMIT_BACKEND=redis         # çok süreçli dağıtımda zorunlu
AI_CACHE_BACKEND=redis
PROCESS_DOCUMENTS_EAGER=false    # işleme Celery worker'a devredilir
AI_JOBS_EAGER=false
EXPORTS_EAGER=false
CORS_ORIGINS=https://app.example.com
FRONTEND_BASE_URL=https://app.example.com
SHARE_PUBLIC_BASE_URL=https://app.example.com/share
```

Anahtar üretimi:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

> `ENCRYPTION_KEY` değiştirilirse mevcut 2FA sırları çözülemez. Rotasyon
> yapmadan önce kullanıcıların 2FA'yı yeniden kurmasını isteyin.

## 3. Sırların yönetimi

`.env` dosyalarını repoya koymayın. Önerilen akış:

- **AWS:** Secrets Manager → ECS task definition `secrets` bölümü
- **Kubernetes:** External Secrets Operator → `Secret` → `envFrom`
- **Self-hosted:** HashiCorp Vault + `vault agent` sidecar

## 4. Veritabanı

```bash
# pgvector uzantısı
psql "$DATABASE_URL" -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Şema
cd backend && alembic upgrade head
```

Migration'lar deploy öncesi ayrı bir job olarak çalıştırılmalıdır; uygulama
konteynerleri migration çalıştırmamalıdır (yalnızca local compose'da öyle).

## 5. Servisler

| Süreç | Komut |
|-------|-------|
| API | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4` |
| Worker | `celery -A app.workers.celery_app worker --loglevel=info` |
| Beat | `celery -A app.workers.celery_app beat` (günlük mutabakat) |

## 6. Staging

```bash
cd infra
cp ../backend/.env.example ../backend/.env.staging   # değerleri doldurun
docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d --build
```

## 7. Sağlık kontrolleri

| Uç | Amaç |
|----|------|
| `GET /health` | Liveness — bağımlılığa dokunmaz |
| `GET /api/v1/ready` | Readiness — Postgres + Redis kontrolü |
| `GET /metrics` | Prometheus (istek sayısı, latency, DB pool) |

Load balancer liveness için `/health`, trafiğe açmadan önce `/api/v1/ready`
kullanmalıdır.

## 8. Gözlemlenebilirlik

- **Sentry:** `SENTRY_DSN` verin ve `pip install ".[observability]"` çalıştırın.
  DSN boşsa entegrasyon tamamen devre dışıdır. Kişisel veri `before_send` ile temizlenir.
- **Prometheus:** `/metrics` ucunu scrape edin.
- **Frontend:** `VITE_SENTRY_DSN` ve `VITE_POSTHOG_KEY` tanımlıysa SDK'lar dinamik
  import ile yüklenir; tanımsızsa bundle'a hiç girmez. PostHog yalnızca çerez onayı
  verilmişse başlatılır.

## 9. Yedekleme

```bash
# Günlük (cron 03:00 UTC)
PGPASSWORD=... BACKUP_S3_BUCKET=s3://docassistant-backups infra/scripts/backup.sh

# Restore testi (staging'de, ayda bir)
PGDATABASE=docassistant_restore infra/scripts/restore.sh backups/<dosya>.dump
```

Object storage tarafında bucket versioning ve lifecycle politikası açık olmalıdır.

## 10. E-posta domain doğrulama

Deliverability için DNS kayıtları:

| Kayıt | Değer |
|-------|-------|
| SPF | `v=spf1 include:_spf.resend.com ~all` |
| DKIM | Sağlayıcının verdiği `resend._domainkey` CNAME |
| DMARC | `v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com` |

Ardından `EMAIL_PROVIDER=resend` ve `EMAIL_API_KEY` ayarlayın. Anahtar yoksa sistem
otomatik olarak konsol sağlayıcısına düşer ve mail göndermez.

## 11. Ödeme sağlayıcısı

1. `BILLING_PROVIDER=stripe`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` ayarlayın.
2. Webhook URL: `https://api.example.com/api/v1/billing/webhook`
3. Dinlenecek olaylar: `checkout.session.completed`,
   `customer.subscription.{created,updated,deleted}`, `invoice.payment_failed`
4. Fiyat ID'lerini `STRIPE_PRICE_PRO` / `STRIPE_PRICE_BUSINESS` ile eşleyin.

## 12. Yayın öncesi kontrol listesi

- [ ] `JWT_SECRET` ve `ENCRYPTION_KEY` üretimde benzersiz
- [ ] `DEBUG=false`, `EXPOSE_DEV_TOKENS=false`
- [ ] `CORS_ORIGINS` yalnızca gerçek frontend domain'i
- [ ] TLS sonlandırma + HSTS aktif (`ENVIRONMENT=production` başlığı ekler)
- [ ] `RATE_LIMIT_BACKEND=redis`
- [ ] Migration job'u deploy pipeline'ında
- [ ] Yedekleme cron'u çalışıyor ve restore testi yapıldı
- [ ] Sentry + Prometheus alarmları tanımlı (error rate, p95 latency, disk)
- [ ] `npm audit` ve `bandit` CI'da yeşil
