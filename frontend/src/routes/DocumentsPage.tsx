import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { documentApi, formatBytes } from "@/features/documents/api";
import type { DocumentStatus } from "@/types/api";

const statusColor: Record<DocumentStatus, string> = {
  uploaded: "text-neutral-400",
  processing: "text-yellow-400",
  ready: "text-green-400",
  failed: "text-red-400",
};

export default function DocumentsPage() {
  const { orgId = "" } = useParams();
  const queryClient = useQueryClient();

  const docsQuery = useQuery({
    queryKey: ["documents", orgId],
    queryFn: () => documentApi.list(orgId),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => documentApi.upload(orgId, file),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["documents", orgId] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (docId: string) => documentApi.remove(orgId, docId),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["documents", orgId] }),
  });

  const favoriteMutation = useMutation({
    mutationFn: ({ docId, value }: { docId: string; value: boolean }) =>
      documentApi.setFavorite(orgId, docId, value),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["documents", orgId] }),
  });

  const onDrop = useCallback(
    (accepted: File[]) => accepted.forEach((f) => uploadMutation.mutate(f)),
    [uploadMutation],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-8">
      <Link to="/dashboard" className="text-sm text-indigo-400 hover:underline">
        ← Panele dön
      </Link>
      <h1 className="text-3xl font-bold">Dokümanlar</h1>

      <Card>
        <div
          {...getRootProps()}
          className={`cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
            isDragActive
              ? "border-indigo-500 bg-indigo-500/10"
              : "border-neutral-700 hover:border-neutral-500"
          }`}
        >
          <input {...getInputProps()} />
          <p className="text-sm text-neutral-400">
            Dosyaları buraya sürükleyin veya seçmek için tıklayın
          </p>
          <p className="mt-1 text-xs text-neutral-600">
            PDF, DOCX, XLSX, PPTX, TXT, MD
          </p>
        </div>
        {uploadMutation.isPending && (
          <p className="mt-2 text-sm text-yellow-400">Yükleniyor…</p>
        )}
      </Card>

      <Card className="space-y-2">
        <h2 className="text-lg font-semibold">Yüklenen Dokümanlar</h2>
        {docsQuery.isLoading && (
          <p className="text-sm text-neutral-400">Yükleniyor…</p>
        )}
        {docsQuery.data?.length === 0 && (
          <p className="text-sm text-neutral-500">Henüz doküman yok.</p>
        )}
        <ul className="space-y-2">
          {docsQuery.data?.map((doc) => (
            <li
              key={doc.id}
              className="flex items-center justify-between rounded-md border border-neutral-800 px-3 py-2 text-sm"
            >
              <div className="min-w-0">
                <p className="truncate font-medium">{doc.filename}</p>
                <p className="text-xs text-neutral-500">
                  {doc.file_type.toUpperCase()} · {formatBytes(doc.size_bytes)} ·{" "}
                  {doc.chunk_count} chunk ·{" "}
                  <span className={statusColor[doc.status]}>{doc.status}</span>
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <button
                  title="Favori"
                  onClick={() =>
                    favoriteMutation.mutate({
                      docId: doc.id,
                      value: !doc.is_favorite,
                    })
                  }
                  className={doc.is_favorite ? "text-yellow-400" : "text-neutral-600"}
                >
                  ★
                </button>
                <Button
                  variant="danger"
                  className="px-2 py-1 text-xs"
                  onClick={() => deleteMutation.mutate(doc.id)}
                >
                  Sil
                </Button>
              </div>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
