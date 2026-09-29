import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";

import { LanguageSwitcher } from "@/components/shared/LanguageSwitcher";
import { NotificationBell } from "@/components/shared/NotificationBell";
import { OnboardingChecklist } from "@/components/shared/OnboardingChecklist";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { authApi, orgApi } from "@/features/auth/api";
import { dashboardApi } from "@/features/dashboard/api";
import { systemApi } from "@/features/system/api";
import { useAuthStore } from "@/stores/authStore";

export default function DashboardPage() {
  const { t } = useTranslation();
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
  const featuresQuery = useQuery({
    queryKey: ["features"],
    queryFn: systemApi.features,
  });

  const primaryOrgId = orgsQuery.data?.[0]?.id;
  const statsQuery = useQuery({
    queryKey: ["dashboard-stats", primaryOrgId],
    queryFn: () => dashboardApi.stats(primaryOrgId!),
    enabled: Boolean(primaryOrgId),
  });

  async function handleLogout() {
    if (refreshToken) await authApi.logout(refreshToken).catch(() => undefined);
    clear();
    navigate("/login");
  }

  const currentUser = meQuery.data ?? user;
  const showOnboarding =
    featuresQuery.data?.flags.includes("onboarding") && Boolean(primaryOrgId);

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">DocAssistant</h1>
        <div className="flex items-center gap-3">
          <LanguageSwitcher />
          <NotificationBell />
          {currentUser?.is_superuser && (
            <Link to="/admin" className="text-sm text-indigo-400 hover:underline">
              {t("nav.admin")}
            </Link>
          )}
          <Button variant="ghost" onClick={handleLogout}>
            {t("nav.logout")}
          </Button>
        </div>
      </div>

      {showOnboarding && (
        <OnboardingChecklist
          orgId={primaryOrgId!}
          hasDocuments={(statsQuery.data?.totals.documents ?? 0) > 0}
          hasAiJobs={(statsQuery.data?.totals.ai_jobs ?? 0) > 0}
        />
      )}

      <Card className="space-y-2">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold">Hesap</h2>
            <p className="text-sm text-neutral-400">
              {currentUser?.email}
              {currentUser && !currentUser.is_verified && (
                <span className="ml-2 rounded bg-yellow-900/50 px-2 py-0.5 text-xs text-yellow-300">
                  Email doğrulanmadı
                </span>
              )}
            </p>
          </div>
          <Link to="/account" className="text-sm text-indigo-400 hover:underline">
            {t("account.title")} →
          </Link>
        </div>
      </Card>

      <Card className="space-y-3">
        <h2 className="text-lg font-semibold">Organizasyonlar</h2>
        {orgsQuery.isLoading && (
          <p className="text-sm text-neutral-400">{t("common.loading")}</p>
        )}
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
              <div className="flex gap-3">
                <Link
                  to={`/organizations/${org.id}/documents`}
                  className="text-sm text-indigo-400 hover:underline"
                >
                  {t("nav.documents")} →
                </Link>
                <Link
                  to={`/organizations/${org.id}/analytics`}
                  className="text-sm text-indigo-400 hover:underline"
                >
                  {t("nav.dashboard")} →
                </Link>
                <Link
                  to={`/organizations/${org.id}/team`}
                  className="text-sm text-indigo-400 hover:underline"
                >
                  {t("nav.team")} →
                </Link>
                <Link
                  to={`/organizations/${org.id}/billing`}
                  className="text-sm text-indigo-400 hover:underline"
                >
                  {t("nav.billing")} →
                </Link>
                <Link
                  to={`/organizations/${org.id}/models`}
                  className="text-sm text-indigo-400 hover:underline"
                >
                  AI Modeli →
                </Link>
              </div>
            </li>
          ))}
        </ul>
      </Card>

      <footer className="flex justify-center gap-4 text-xs text-neutral-600">
        <Link to="/privacy" className="hover:text-neutral-400">
          {t("nav.privacy")}
        </Link>
        <Link to="/terms" className="hover:text-neutral-400">
          {t("nav.terms")}
        </Link>
      </footer>
    </div>
  );
}
