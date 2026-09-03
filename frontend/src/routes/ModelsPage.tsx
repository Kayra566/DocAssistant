import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { formatBytes } from "@/features/documents/api";
import { filenameOf, modelApi, sourceLabel } from "@/features/models/api";
import { getApiErrorMessage } from "@/lib/api-error";
import type { ModelInfo } from "@/types/api";

export default function ModelsPage() {
  const { orgId = "" } = useParams();
  const queryClient = useQueryClient();

  const modelsQuery = useQuery({ queryKey: ["models"], queryFn: modelApi.list });

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["models"] });

  const activateMutation = useMutation({
    mutationFn: (modelId: string) => modelApi.setActive(orgId, modelId),
    onSuccess: invalidate,
  });

  const importMutation = useMutation({
    mutationFn: (filename: string) => modelApi.importFile(orgId, filename),
    onSuccess: invalidate,
  });

  const error = activateMutation.error ?? importMutation.error;
  const errorMsg = error ? getApiErrorMessage(error, "İşlem başarısız.") : null;

  const data = modelsQuery.data;
  const pending = activateMutation.isPending || importMutation.isPending;

  function renderAction(model: ModelInfo) {
    if (model.id === data?.active_model_id) {
      return (
        <span className="rounded-md border border-green-800 px-3 py-1.5 text-xs text-green-400">
          Kullanımda
        </span>
      );
    }
    if (!model.ready) {
      return (
        <Button
          variant="ghost"
          className="border border-neutral-700 px-3 py-1.5 text-xs"
          disabled={pending || !data?.ollama_available}
          onClick={() => importMutation.mutate(filenameOf(model))}
        >
          {importMutation.isPending ? "Aktarılıyor…" : "İçe aktar"}
        </Button>
      );
    }
    return (
      <Button
        className="px-3 py-1.5 text-xs"
        disabled={pending}
        onClick={() => activateMutation.mutate(model.id)}
      >
        Kullan
      </Button>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-8">
      <Link to="/dashboard" className="text-sm text-indigo-400 hover:underline">
        ← Panele dön
      </Link>
      <h1 className="text-3xl font-bold">AI Modeli</h1>

      <Card className="space-y-2">
        <h2 className="text-lg font-semibold">Model klasörü</h2>
        <p className="text-sm text-neutral-400">
          <code className="rounded bg-neutral-800 px-1.5 py-0.5 text-xs">
            {data?.models_dir ?? "…"}
          </code>{" "}
          klasörüne <code className="text-xs">.gguf</code> uzantılı bir model dosyası
          bırakın; sayfayı yenilediğinizde aşağıda görünür.
        </p>
        <p className="text-xs text-neutral-500">
          Ollama:{" "}
          {data?.ollama_available ? (
            <span className="text-green-400">çalışıyor</span>
          ) : (
            <span className="text-yellow-400">
              çalışmıyor — dosya modellerini içe aktarmak için gerekli
            </span>
          )}
        </p>
      </Card>

      {errorMsg && (
        <p role="alert" className="text-sm text-red-400">
          {errorMsg}
        </p>
      )}

      <Card className="space-y-2">
        <h2 className="text-lg font-semibold">Kullanılabilir modeller</h2>
        {modelsQuery.isLoading && (
          <p className="text-sm text-neutral-400">Yükleniyor…</p>
        )}
        <ul className="space-y-2">
          {data?.models.map((model) => (
            <li
              key={model.id}
              className="flex items-center justify-between gap-3 rounded-md border border-neutral-800 px-3 py-2"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{model.name}</p>
                <p className="text-xs text-neutral-500">
                  {sourceLabel(model.source)}
                  {model.size_bytes > 0 && ` · ${formatBytes(model.size_bytes)}`}
                  {` · ${model.detail}`}
                </p>
              </div>
              <div className="shrink-0">{renderAction(model)}</div>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
