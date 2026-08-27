import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card } from "@/components/ui/card";
import {
  dashboardApi,
  describeActivity,
  jobTypeLabel,
  shortDate,
} from "@/features/dashboard/api";
import { formatBytes } from "@/features/documents/api";
import { usagePercent } from "@/features/billing/api";
import type { DashboardQuota } from "@/types/api";

const PIE_COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ec4899", "#06b6d4", "#a855f7"];

const AXIS_STYLE = { fontSize: 11, fill: "#a3a3a3" };
const TOOLTIP_STYLE = {
  backgroundColor: "#171717",
  border: "1px solid #404040",
  borderRadius: 8,
  fontSize: 12,
};

function QuotaBar({
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
  const render = format ?? ((value: number) => value.toLocaleString("tr-TR"));
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

function StatTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-neutral-800 px-4 py-3">
      <p className="text-xs uppercase text-neutral-500">{label}</p>
      <p className="text-2xl font-bold">{value.toLocaleString("tr-TR")}</p>
    </div>
  );
}

function QuotaCard({ quota }: { quota: DashboardQuota }) {
  return (
    <Card className="space-y-3">
      <h2 className="text-lg font-semibold">Kota kullanımı</h2>
      <QuotaBar
        label="Doküman"
        used={quota.documents_used}
        limit={quota.documents_limit}
      />
      <QuotaBar
        label="Depolama"
        used={quota.storage_bytes_used}
        limit={quota.storage_bytes_limit}
        format={formatBytes}
      />
      <QuotaBar
        label="AI isteği (bu ay)"
        used={quota.ai_requests_used}
        limit={quota.ai_requests_limit}
      />
      <QuotaBar
        label="AI token (bu ay)"
        used={quota.ai_tokens_used}
        limit={quota.ai_tokens_limit}
      />
    </Card>
  );
}

export default function AnalyticsPage() {
  const { orgId = "" } = useParams();

  const statsQuery = useQuery({
    queryKey: ["dashboard-stats", orgId],
    queryFn: () => dashboardApi.stats(orgId),
  });

  const activityQuery = useQuery({
    queryKey: ["activity", orgId],
    queryFn: () => dashboardApi.activity(orgId),
  });

  const stats = statsQuery.data;
  const trend = (stats?.usage_trend ?? []).map((point) => ({
    ...point,
    label: shortDate(point.date),
  }));
  const jobs = (stats?.job_distribution ?? []).map((item) => ({
    ...item,
    label: jobTypeLabel(item.key),
  }));

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-8">
      <Link to="/dashboard" className="text-sm text-indigo-400 hover:underline">
        ← Panele dön
      </Link>
      <h1 className="text-3xl font-bold">Kullanım Panosu</h1>

      {statsQuery.isLoading && (
        <p className="text-sm text-neutral-400">Yükleniyor…</p>
      )}

      {stats && (
        <>
          <div className="grid gap-3 sm:grid-cols-4">
            <StatTile label="Doküman" value={stats.totals.documents} />
            <StatTile label="AI işlemi" value={stats.totals.ai_jobs} />
            <StatTile label="Aktif paylaşım" value={stats.totals.share_links} />
            <StatTile label="Ekip üyesi" value={stats.totals.members} />
          </div>

          <Card className="space-y-3">
            <h2 className="text-lg font-semibold">Son 30 gün</h2>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                  <XAxis dataKey="label" tick={AXIS_STYLE} interval={4} />
                  <YAxis tick={AXIS_STYLE} allowDecimals={false} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Line
                    type="monotone"
                    dataKey="documents"
                    name="Doküman"
                    stroke="#6366f1"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="ai_jobs"
                    name="AI işlemi"
                    stroke="#22c55e"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card className="space-y-3">
              <h2 className="text-lg font-semibold">AI işlem dağılımı</h2>
              {jobs.length === 0 ? (
                <p className="text-sm text-neutral-500">Henüz AI işlemi yok.</p>
              ) : (
                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={jobs}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                      <XAxis dataKey="label" tick={AXIS_STYLE} />
                      <YAxis tick={AXIS_STYLE} allowDecimals={false} />
                      <Tooltip contentStyle={TOOLTIP_STYLE} />
                      <Bar dataKey="count" name="İşlem" fill="#6366f1" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </Card>

            <Card className="space-y-3">
              <h2 className="text-lg font-semibold">Doküman durumu</h2>
              {stats.document_status.length === 0 ? (
                <p className="text-sm text-neutral-500">Henüz doküman yok.</p>
              ) : (
                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={stats.document_status}
                        dataKey="count"
                        nameKey="key"
                        outerRadius={80}
                        label
                      >
                        {stats.document_status.map((entry, index) => (
                          <Cell
                            key={entry.key}
                            fill={PIE_COLORS[index % PIE_COLORS.length]}
                          />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={TOOLTIP_STYLE} />
                      <Legend wrapperStyle={{ fontSize: 12 }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}
            </Card>
          </div>

          <QuotaCard quota={stats.quota} />
        </>
      )}

      <Card className="space-y-2">
        <h2 className="text-lg font-semibold">İşlem geçmişi</h2>
        {activityQuery.data?.length === 0 && (
          <p className="text-sm text-neutral-500">Henüz kayıt yok.</p>
        )}
        <ul className="space-y-1">
          {activityQuery.data?.map((entry) => (
            <li
              key={entry.id}
              className="flex items-center justify-between gap-3 rounded-md border border-neutral-800 px-3 py-2 text-sm"
            >
              <span className="min-w-0 truncate">{describeActivity(entry)}</span>
              <span className="shrink-0 text-xs text-neutral-500">
                {new Date(entry.created_at).toLocaleString("tr-TR")}
              </span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
