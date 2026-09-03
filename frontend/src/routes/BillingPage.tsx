import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { billingApi, formatPrice, usagePercent } from "@/features/billing/api";
import { formatBytes } from "@/features/documents/api";
import { getApiErrorMessage } from "@/lib/api-error";
import type { Plan } from "@/types/api";

const STATUS_LABELS: Record<string, string> = {
  active: "Aktif",
  trialing: "Deneme",
  past_due: "Ödeme bekliyor",
  canceled: "İptal edildi",
  incomplete: "Tamamlanmadı",
};

function UsageBar({
  label,
  used,
  limit,
  format,
}: {
  label: string;
  used: number;
  limit: number;
  format?: (value: number) => string;
}) {
  const percent = usagePercent(used, limit);
  const render = format ?? ((v: number) => v.toLocaleString("tr-TR"));
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-neutral-400">
        <span>{label}</span>
        <span>
          {render(used)} / {render(limit)}
        </span>
      </div>
      <div className="h-2 w-full rounded-full bg-neutral-800">
        <div
          className={`h-2 rounded-full ${percent >= 90 ? "bg-red-500" : "bg-indigo-500"}`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}

export default function BillingPage() {
  const { orgId = "" } = useParams();
  const queryClient = useQueryClient();

  const plansQuery = useQuery({ queryKey: ["plans"], queryFn: billingApi.plans });
  const usageQuery = useQuery({
    queryKey: ["billing-usage", orgId],
    queryFn: () => billingApi.usage(orgId),
  });

  const checkoutMutation = useMutation({
    mutationFn: (plan: Plan) => billingApi.checkout(orgId, plan),
    onSuccess: ({ url }) => {
      window.location.href = url;
    },
  });

  const portalMutation = useMutation({
    mutationFn: () => billingApi.portal(orgId),
    onSuccess: ({ url }) => {
      window.location.href = url;
    },
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: ["billing-usage", orgId] }),
  });

  const error = [checkoutMutation.error, portalMutation.error].find(Boolean);
  const errorMsg =
    error ? getApiErrorMessage(error, "Bir hata oluştu.") : null;

  const usage = usageQuery.data;

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-8">
      <Link to="/dashboard" className="text-sm text-indigo-400 hover:underline">
        ← Panele dön
      </Link>
      <h1 className="text-3xl font-bold">Plan ve Kullanım</h1>

      {usage && (
        <Card className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold capitalize">{usage.plan}</h2>
              <p className="text-xs text-neutral-500">
                {STATUS_LABELS[usage.status] ?? usage.status}
                {usage.cancel_at_period_end && " · dönem sonunda iptal edilecek"}
                {usage.current_period_end &&
                  ` · yenileme: ${new Date(usage.current_period_end).toLocaleDateString("tr-TR")}`}
              </p>
            </div>
            <Button
              variant="ghost"
              onClick={() => portalMutation.mutate()}
              disabled={portalMutation.isPending}
            >
              Aboneliği yönet
            </Button>
          </div>

          <UsageBar
            label="Doküman"
            used={usage.documents_used}
            limit={usage.documents_limit}
          />
          <UsageBar
            label="Depolama"
            used={usage.storage_bytes_used}
            limit={usage.storage_bytes_limit}
            format={formatBytes}
          />
          <UsageBar
            label="AI isteği (bu ay)"
            used={usage.ai_requests_used}
            limit={usage.ai_requests_limit}
          />
          <UsageBar
            label="AI token (bu ay)"
            used={usage.ai_tokens_used}
            limit={usage.ai_tokens_limit}
          />
        </Card>
      )}

      {errorMsg && <p className="text-sm text-red-400">{errorMsg}</p>}

      <div className="grid gap-4 sm:grid-cols-3">
        {plansQuery.data?.map((spec) => {
          const isCurrent = usage?.plan === spec.key;
          return (
            <Card key={spec.key} className="flex flex-col justify-between space-y-3">
              <div className="space-y-2">
                <h3 className="text-lg font-semibold">{spec.name}</h3>
                <p className="text-2xl font-bold">{formatPrice(spec)}</p>
                <ul className="space-y-1 text-xs text-neutral-400">
                  <li>{spec.documents.toLocaleString("tr-TR")} doküman</li>
                  <li>{spec.storage_mb.toLocaleString("tr-TR")} MB depolama</li>
                  <li>{spec.ai_requests.toLocaleString("tr-TR")} AI isteği/ay</li>
                  {spec.features.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              </div>
              {isCurrent ? (
                <span className="rounded-md border border-neutral-700 px-3 py-2 text-center text-xs text-neutral-400">
                  Mevcut plan
                </span>
              ) : (
                <Button
                  disabled={spec.key === "free" || checkoutMutation.isPending}
                  onClick={() => checkoutMutation.mutate(spec.key)}
                >
                  {spec.key === "free" ? "Varsayılan" : "Yükselt"}
                </Button>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
}
