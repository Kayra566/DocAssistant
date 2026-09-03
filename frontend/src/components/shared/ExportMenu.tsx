import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { EXPORT_FORMATS, exportApi } from "@/features/exports/api";
import { getApiErrorMessage } from "@/lib/api-error";
import type { ExportFormat } from "@/types/api";

export function ExportMenu({
  orgId,
  aiJobId,
}: {
  orgId: string;
  aiJobId: string;
}) {
  const [pending, setPending] = useState<ExportFormat | null>(null);

  const mutation = useMutation({
    mutationFn: async (format: ExportFormat) => {
      const job = await exportApi.create(orgId, aiJobId, format);
      if (job.status !== "done") throw new Error(job.error ?? "Export başarısız.");
      await exportApi.download(orgId, job);
    },
    onSettled: () => setPending(null),
  });

  const errorMsg =
    mutation.error
      ? getApiErrorMessage(mutation.error, "Dışa aktarma başarısız.")
      : null;

  return (
    <div className="space-y-1">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-neutral-500">Dışa aktar:</span>
        {EXPORT_FORMATS.map((format) => (
          <Button
            key={format.key}
            variant="ghost"
            className="border border-neutral-700 px-2 py-1 text-xs"
            disabled={mutation.isPending}
            onClick={() => {
              setPending(format.key);
              mutation.mutate(format.key);
            }}
          >
            {pending === format.key ? "…" : format.label}
          </Button>
        ))}
      </div>
      {errorMsg && <p className="text-xs text-red-400">{errorMsg}</p>}
    </div>
  );
}
