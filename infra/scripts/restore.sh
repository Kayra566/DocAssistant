#!/usr/bin/env bash
# Bir pg_dump arşivini hedef veritabanına geri yükler.
#
# UYARI: --clean hedefteki nesneleri düşürür. Önce staging'de test edin.
#
# Kullanım:
#   PGDATABASE=docassistant_restore ./restore.sh ./backups/docassistant-2026....dump

set -euo pipefail

archive="${1:-}"
if [[ -z "${archive}" || ! -f "${archive}" ]]; then
  echo "Kullanım: $0 <yedek-dosyasi.dump>" >&2
  exit 1
fi

PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-dev}"
PGDATABASE="${PGDATABASE:-docassistant_restore}"

echo "==> Arşiv doğrulanıyor"
pg_restore --list "${archive}" > /dev/null

echo "==> ${PGDATABASE} veritabanına geri yükleniyor"
pg_restore \
  --host="${PGHOST}" --port="${PGPORT}" --username="${PGUSER}" \
  --dbname="${PGDATABASE}" \
  --clean --if-exists --no-owner --exit-on-error

echo "==> Doğrulama sorgusu"
psql --host="${PGHOST}" --port="${PGPORT}" --username="${PGUSER}" \
  --dbname="${PGDATABASE}" \
  --command="SELECT 'users' AS tablo, count(*) FROM users
             UNION ALL SELECT 'documents', count(*) FROM documents
             UNION ALL SELECT 'activity_logs', count(*) FROM activity_logs;"

echo "Geri yükleme tamamlandı."
