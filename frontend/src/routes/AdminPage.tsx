import { useQuery } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { Link } from "react-router-dom";

import { Card } from "@/components/ui/card";
import { adminApi } from "@/features/dashboard/api";
import { formatBytes } from "@/features/documents/api";

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-neutral-800 px-4 py-3">
      <p className="text-xs uppercase text-neutral-500">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}

export default function AdminPage() {
  const statsQuery = useQuery({
    queryKey: ["admin-stats"],
    queryFn: adminApi.stats,
    retry: false,
  });

  const orgsQuery = useQuery({
    queryKey: ["admin-orgs"],
    queryFn: adminApi.organizations,
    retry: false,
    enabled: statsQuery.isSuccess,
  });

  const forbidden =
    statsQuery.error instanceof AxiosError &&
    statsQuery.error.response?.status === 403;

  const stats = statsQuery.data;

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-8">
      <Link to="/dashboard" className="text-sm text-indigo-400 hover:underline">
        ← Panele dön
      </Link>
      <h1 className="text-3xl font-bold">Platform Yönetimi</h1>

      {forbidden && (
        <p className="text-sm text-red-400">
          Bu sayfa yalnızca platform yöneticilerine açıktır.
        </p>
      )}

      {stats && (
        <>
          <div className="grid gap-3 sm:grid-cols-3">
            <StatTile label="Kullanıcı" value={stats.users.toLocaleString("tr-TR")} />
            <StatTile
              label="Doğrulanmış"
              value={stats.verified_users.toLocaleString("tr-TR")}
            />
            <StatTile
              label="Organizasyon"
              value={stats.organizations.toLocaleString("tr-TR")}
            />
            <StatTile
              label="Doküman"
              value={stats.documents.toLocaleString("tr-TR")}
            />
            <StatTile label="AI işlemi" value={stats.ai_jobs.toLocaleString("tr-TR")} />
            <StatTile label="Depolama" value={formatBytes(stats.storage_bytes)} />
          </div>

          <Card className="space-y-2">
            <h2 className="text-lg font-semibold">Plan dağılımı</h2>
            <ul className="space-y-1 text-sm text-neutral-300">
              {stats.plan_distribution.map((item) => (
                <li key={item.key} className="flex justify-between">
                  <span className="capitalize">{item.key}</span>
                  <span className="text-neutral-500">{item.count}</span>
                </li>
              ))}
            </ul>
          </Card>

          <Card className="space-y-2">
            <h2 className="text-lg font-semibold">Organizasyonlar</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase text-neutral-500">
                  <tr>
                    <th className="border-b border-neutral-800 py-1 pr-4">Ad</th>
                    <th className="border-b border-neutral-800 py-1 pr-4">Plan</th>
                    <th className="border-b border-neutral-800 py-1 pr-4">Doküman</th>
                    <th className="border-b border-neutral-800 py-1 pr-4">Üye</th>
                    <th className="border-b border-neutral-800 py-1">Kayıt</th>
                  </tr>
                </thead>
                <tbody>
                  {orgsQuery.data?.map((org) => (
                    <tr key={org.id}>
                      <td className="border-b border-neutral-900 py-1 pr-4">
                        {org.name}
                      </td>
                      <td className="border-b border-neutral-900 py-1 pr-4 uppercase text-neutral-500">
                        {org.plan}
                      </td>
                      <td className="border-b border-neutral-900 py-1 pr-4">
                        {org.documents}
                      </td>
                      <td className="border-b border-neutral-900 py-1 pr-4">
                        {org.members}
                      </td>
                      <td className="border-b border-neutral-900 py-1 text-neutral-500">
                        {new Date(org.created_at).toLocaleDateString("tr-TR")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
