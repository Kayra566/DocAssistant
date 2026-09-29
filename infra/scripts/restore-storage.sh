#!/usr/bin/env bash
# Daha önce mirror edilmiş object storage yedeğini hedef bucket'a geri yükler.
#
# Kullanım:
#   MC_ALIAS=docassistant MC_BUCKET=documents ./restore-storage.sh ./backups/object-storage-...

set -euo pipefail

source_dir="${1:-}"
if [[ -z "${source_dir}" || ! -d "${source_dir}" ]]; then
  echo "Kullanım: $0 <object-storage-yedek-dizini>" >&2
  exit 1
fi

MC_ALIAS="${MC_ALIAS:?MC_ALIAS gerekli}"
MC_BUCKET="${MC_BUCKET:-docassistant}"

echo "==> ${source_dir} → ${MC_ALIAS}/${MC_BUCKET}"
mc mirror --overwrite "${source_dir}" "${MC_ALIAS}/${MC_BUCKET}"
echo "Object storage geri yükleme tamamlandı."
