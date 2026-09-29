import { useQuery } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { useParams, useSearchParams } from "react-router-dom";

import { Card } from "@/components/ui/card";
import { formatBytes } from "@/features/documents/api";
import { shareApi } from "@/features/sharing/api";
import { getApiErrorMessage } from "@/lib/api-error";

export default function SharedDocumentPage() {
  const { token = "" } = useParams();
  const [searchParams] = useSearchParams();
  const proof = searchParams.get("proof") ?? "";

  const shareQuery = useQuery({
    queryKey: ["public-share", token, proof],
    queryFn: () => shareApi.publicInfo(token, proof || undefined),
    retry: false,
  });

  const status =
    shareQuery.error instanceof AxiosError
      ? shareQuery.error.response?.status
      : undefined;
  const errorMsg = shareQuery.error
    ? getApiErrorMessage(shareQuery.error, "Bağlantı geçersiz veya süresi dolmuş.")
    : null;

  const doc = shareQuery.data;

  return (
    <div className="mx-auto max-w-lg space-y-6 p-8">
      <h1 className="text-3xl font-bold">Paylaşılan Doküman</h1>

      {shareQuery.isLoading && (
        <p className="text-sm text-neutral-400">Yükleniyor…</p>
      )}

      {status === 401 && (
        <Card>
          <p className="text-sm text-red-400">{errorMsg}</p>
        </Card>
      )}

      {errorMsg && status !== 401 && (
        <p className="text-sm text-red-400">{errorMsg}</p>
      )}

      {doc && (
        <Card className="space-y-3">
          <div>
            <h2 className="text-lg font-semibold">{doc.filename}</h2>
            <p className="text-xs text-neutral-500">
              {doc.organization_name} tarafından paylaşıldı
            </p>
          </div>
          <ul className="space-y-1 text-sm text-neutral-400">
            <li>Tür: {doc.file_type.toUpperCase()}</li>
            <li>Boyut: {formatBytes(doc.size_bytes)}</li>
            <li>Sayfa: {doc.page_count}</li>
            <li>
              Geçerlilik:{" "}
              {new Date(doc.expires_at).toLocaleString("tr-TR")} sonuna kadar
            </li>
          </ul>

          {doc.can_download ? (
            <a
              href={shareApi.publicDownloadUrl(token, proof || undefined)}
              className="inline-flex items-center justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
            >
              Dokümanı indir
            </a>
          ) : (
            <p className="rounded-md border border-neutral-800 px-3 py-2 text-xs text-neutral-500">
              Bu bağlantı yalnızca görüntüleme izni veriyor; indirme kapalı.
            </p>
          )}
        </Card>
      )}
    </div>
  );
}
