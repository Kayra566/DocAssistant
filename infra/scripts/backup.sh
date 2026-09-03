#!/usr/bin/env bash
# Postgres yedeği alır ve (yapılandırılmışsa) S3'e yükler.
# pgvector verisi aynı dump içinde yer alır; ayrı yedek gerekmez.
#
# Kullanım:
#   PGPASSWORD=... ./backup.sh
#   BACKUP_S3_BUCKET=s3://docassistant-backups ./backup.sh

set -euo pipefail

PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-dev}"
PGDATABASE="${PGDATABASE:-docassistant}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
archive="${BACKUP_DIR}/${PGDATABASE}-${timestamp}.dump"

mkdir -p "${BACKUP_DIR}"

echo "==> pg_dump ${PGDATABASE} → ${archive}"
pg_dump \
  --host="${PGHOST}" --port="${PGPORT}" --username="${PGUSER}" \
  --dbname="${PGDATABASE}" \
  --format=custom --compress=9 --no-owner \
  --file="${archive}"

echo "==> Yedek doğrulanıyor"
pg_restore --list "${archive}" > /dev/null
echo "    OK ($(du -h "${archive}" | cut -f1))"

if [[ -n "${BACKUP_S3_BUCKET:-}" ]]; then
  echo "==> ${BACKUP_S3_BUCKET} adresine yükleniyor"
  aws s3 cp "${archive}" "${BACKUP_S3_BUCKET}/postgres/"
fi

echo "==> ${RETENTION_DAYS} günden eski yerel yedekler siliniyor"
find "${BACKUP_DIR}" -name "${PGDATABASE}-*.dump" -mtime "+${RETENTION_DAYS}" -delete

echo "Tamamlandı: ${archive}"
