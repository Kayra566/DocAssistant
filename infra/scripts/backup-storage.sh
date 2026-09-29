#!/usr/bin/env bash
# MinIO/S3 bucket içeriğini sürümlü bir dizine mirror eder.
# Gereksinim: MinIO Client (`mc`) ve önceden tanımlanmış bir alias.
#
# Kullanım:
#   MC_ALIAS=docassistant MC_BUCKET=documents ./backup-storage.sh

set -euo pipefail

MC_ALIAS="${MC_ALIAS:?MC_ALIAS gerekli}"
MC_BUCKET="${MC_BUCKET:-docassistant}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="${BACKUP_DIR}/object-storage-${timestamp}"

mkdir -p "${target}"
echo "==> ${MC_ALIAS}/${MC_BUCKET} → ${target}"
mc mirror --preserve "${MC_ALIAS}/${MC_BUCKET}" "${target}"

find "${BACKUP_DIR}" -maxdepth 1 -type d \
  -name "object-storage-*" -mtime "+${RETENTION_DAYS}" -exec rm -rf {} +
echo "Tamamlandı: ${target}"
