import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { authApi, orgApi } from "@/features/auth/api";
import { useAuthStore } from "@/stores/authStore";

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user, refreshToken, clear, setUser } = useAuthStore();

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const u = await authApi.me();
      setUser(u);
      return u;
    },
  });

  const orgsQuery = useQuery({ queryKey: ["orgs"], queryFn: orgApi.list });

  async function handleLogout() {
    if (refreshToken) await authApi.logout(refreshToken).catch(() => undefined);
    clear();
    navigate("/login");
  }

  const currentUser = meQuery.data ?? user;

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">DocAssistant</h1>
        <Button variant="ghost" onClick={handleLogout}>
          Çıkış Yap
        </Button>
      </div>

      <Card className="space-y-2">
        <h2 className="text-lg font-semibold">Hesap</h2>
        <p className="text-sm text-neutral-400">
          {currentUser?.email}
          {currentUser && !currentUser.is_verified && (
            <span className="ml-2 rounded bg-yellow-900/50 px-2 py-0.5 text-xs text-yellow-300">
              Email doğrulanmadı
            </span>
          )}
        </p>
      </Card>

      <Card className="space-y-3">
        <h2 className="text-lg font-semibold">Organizasyonlar</h2>
        {orgsQuery.isLoading && <p className="text-sm text-neutral-400">Yükleniyor…</p>}
        <ul className="space-y-2">
          {orgsQuery.data?.map((org) => (
            <li
              key={org.id}
              className="flex items-center justify-between rounded-md border border-neutral-800 px-3 py-2"
            >
              <span>
                {org.name}{" "}
                <span className="text-xs uppercase text-neutral-500">{org.plan}</span>
              </span>
              <Link
                to={`/organizations/${org.id}/team`}
                className="text-sm text-indigo-400 hover:underline"
              >
                Ekip →
              </Link>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
