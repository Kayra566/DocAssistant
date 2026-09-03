# Troubleshooting

Sık karşılaşılan sorunlar ve çözümleri.

## Kurulum ve Docker

### `docker compose up` başlarken env_file hatası veriyor

```
error mounting ... .env: not a directory
```

`backend/.env` bir **dizin** olarak oluşmuş. Silin ve dosyayı örnekten kopyalayın:

```powershell
Remove-Item -Recurse -Force ..\backend\.env
Copy-Item ..\backend\.env.example ..\backend\.env
```

### Kayıt olurken "relation \"users\" does not exist"

Şema oluşmamış. Local compose migration'ı otomatik çalıştırır; elle tetiklemek için:

```bash
cd backend && alembic upgrade head
```

### Docker Desktop çalışmıyor

`error during connect: ... docker_engine` hatası Docker Desktop'ın kapalı olduğunu
gösterir. Uygulamayı başlatıp ikonun "Engine running" durumuna geçmesini bekleyin.

## Kimlik doğrulama

### İstekler 401 dönüyor ama parola doğru

Access token'ın ömrü 15 dakikadır. Frontend refresh akışını otomatik yürütür;
manuel test yaparken `POST /api/v1/auth/refresh` ile yenileyin.

### Hesap kilitlendi (HTTP 423)

5 hatalı denemeden sonra hesap `LOCKOUT_MINUTES` kadar kilitlenir. Bekleyin veya
DB'de `users.locked_until` alanını temizleyin.

### E-posta doğrulama linki gelmiyor

`EMAIL_API_KEY` boşsa sistem konsol sağlayıcısına düşer ve mail göndermez.
Local'de `EXPOSE_DEV_TOKENS=true` iken token API yanıtındaki
`dev_verification_token` alanında döner.

## Rate limiting

### Testler veya scriptler 429 alıyor

Auth uçları dakikada `RATE_LIMIT_AUTH_REQUESTS` (varsayılan 10) istekle sınırlıdır.
Otomasyon için `RATE_LIMIT_ENABLED=false` ayarlayın veya limiti yükseltin.

### Limit birden fazla sunucuda tutarsız

`RATE_LIMIT_BACKEND=memory` her süreçte ayrı sayaç tutar. Çok süreçli dağıtımda
`redis` kullanın.

## Doküman işleme

### Doküman "failed" durumunda kalıyor

`documents.error` alanı nedeni içerir. Sık nedenler:

- Şifre korumalı PDF → metin çıkarılamaz
- Taranmış (görüntü) PDF → `ENABLE_OCR=true` gerekir
- Bozuk dosya → magic-bytes doğrulaması uzantıyla uyuşmuyor

### Doküman "processing" durumunda takılıyor

`PROCESS_DOCUMENTS_EAGER=false` ise Celery worker çalışıyor olmalıdır:

```bash
docker compose logs worker
```

### 402 Payment Required

Plan kotası doldu (doküman sayısı, depolama, aylık AI isteği veya token).
`GET /api/v1/billing/{org_id}/usage` ile hangi limitin dolduğunu görün.

## AI

### Yanıtlar anlamsız veya çok kısa

Varsayılan `LLM_PROVIDER=fake` deterministik bir sahte sağlayıcıdır. Gerçek model
için Ollama çalıştırın:

```bash
ollama serve && ollama pull llama3.1:8b
# .env: LLM_PROVIDER=ollama
```

### Aynı soruya hep aynı cevap dönüyor

Sonuçlar `AI_CACHE_TTL_SECONDS` boyunca önbelleklenir. Yanıtta `cache_hit: true`
görürsünüz. Önbelleği atlamak için TTL'i düşürün.

## Export

### PDF'de Türkçe karakterler bozuk

Export, reportlab ile gelen Vera fontunu kullanır ve Türkçe glifleri kapsar.
Bozukluk görüyorsanız özel bir font kaydedilmiş olabilir; `app/exports/renderers.py`
içindeki `_register_fonts` fonksiyonunu kontrol edin.

### Export "failed" oluyor

`export_jobs.error` alanına bakın. En sık neden: AI işi henüz `done` değil.

## Veritabanı ve migration

### "Multiple heads" hatası

```bash
alembic heads          # birden fazla head varsa
alembic merge -m "merge heads" <rev1> <rev2>
```

### Audit log güncellenemiyor

`activity_logs` tablosu Postgres'te trigger ile append-only yapılmıştır; UPDATE ve
DELETE reddedilir. Bu kasıtlıdır. Zinciri doğrulamak için:

```
GET /api/v1/admin/audit/{org_id}/verify
```

## Frontend

### `npm run build` tip hatası veriyor

`tsc -b` artımlı derleme kullanır. Bozuk cache için:

```bash
rm -rf node_modules/.tmp tsconfig.tsbuildinfo && npm run build
```

### CORS hatası

`CORS_ORIGINS` frontend origin'ini tam olarak içermelidir (şema + port dahil).

### Bildirim rozeti güncellenmiyor

Okunmamış sayısı 60 saniyede bir yenilenir. Anında görmek için sayfayı yenileyin.

## Gözlemlenebilirlik

### `/metrics` 404 dönüyor

`METRICS_ENABLED=false` ayarlanmış demektir.

### Sentry'ye olay düşmüyor

`SENTRY_DSN` tanımlı olmalı **ve** `pip install ".[observability]"` çalıştırılmış
olmalıdır. Paket yoksa başlangıçta uyarı loglanır ve entegrasyon atlanır.
