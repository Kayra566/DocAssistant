# DocAssistant Mimarisi

Bu belge güncel çalışma zamanı topolojisini ve kritik doküman/AI akışlarını gösterir.

## Deployment

```mermaid
flowchart LR
    U[Kullanıcı] -->|HTTPS| FE[React / nginx]
    FE -->|REST + SSE| API[FastAPI]
    API --> PG[(PostgreSQL + pgvector)]
    API --> R[(Redis)]
    API --> S3[(MinIO / S3)]
    API -->|INSTREAM| C[ClamAV]
    API --> O[Ollama]
    API --> E[Resend / SendGrid]
    API --> ST[Sentry / PostHog]
    W[Celery Worker] --> PG
    W --> R
    W --> S3
    W --> O
    B[Celery Beat] --> R
    R --> W
```

ClamAV yerel ortamda `security`, Ollama ise `ai` Docker Compose profiliyle
etkinleştirilir. Production ortamında aynı arayüzler yönetilen PostgreSQL, Redis ve
S3 servislerine yönlendirilebilir.

## Doküman Yükleme ve İşleme

```mermaid
sequenceDiagram
    actor User as Kullanıcı
    participant UI as React
    participant API as FastAPI
    participant AV as ClamAV
    participant Store as MinIO/S3
    participant DB as PostgreSQL
    participant Worker as Celery

    User->>UI: Dosya seçer
    UI->>API: multipart upload
    API->>API: Boyut + magic-byte doğrulama
    opt Malware scan aktif
        API->>AV: INSTREAM taraması
        AV-->>API: OK veya FOUND
    end
    API->>Store: Orijinal dosyayı kaydet
    API->>DB: uploaded kaydı
    API->>Worker: process_document
    Worker->>Store: Dosyayı oku
    Worker->>Worker: Metin/OCR, chunk, embedding
    Worker->>DB: Chunk + vektör + ready durumu
    API-->>UI: Polling ile güncel durum
```

Tarama etkin olduğunda ClamAV zaman aşımı veya bağlantı hatası yüklemeyi durdurur;
tarama yapılmamış dosya depoya yazılmaz.

## RAG Chat ve Sayfa Referansı

```mermaid
sequenceDiagram
    actor User as Kullanıcı
    participant UI as React
    participant API as FastAPI
    participant DB as PostgreSQL/pgvector
    participant LLM as Ollama
    participant Store as MinIO/S3

    User->>UI: Doküman hakkında soru
    UI->>API: Chat isteği
    API->>DB: Tenant-scoped similarity search
    DB-->>API: Sayfa metadatalı chunk'lar
    API->>LLM: Güvenli prompt + context
    LLM-->>API: Yanıt
    API-->>UI: Yanıt + citations
    User->>UI: Sayfa referansına tıklar
    UI->>API: İmzalı preview URL isteği
    API-->>UI: Kısa ömürlü URL
    UI->>API: PDF preview + #page
    API->>Store: PDF'i oku
    API-->>UI: inline application/pdf
```
