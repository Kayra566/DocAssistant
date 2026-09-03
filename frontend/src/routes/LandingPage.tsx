import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { LanguageSwitcher } from "@/components/shared/LanguageSwitcher";
import { Card } from "@/components/ui/card";
import { useAuthStore } from "@/stores/authStore";

const FEATURE_KEYS = ["chat", "tools", "team"] as const;

export default function LandingPage() {
  const { t } = useTranslation();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());

  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-5xl items-center justify-between p-6">
        <span className="text-lg font-bold">DocAssistant</span>
        <div className="flex items-center gap-4">
          <LanguageSwitcher />
          <Link
            to={isAuthenticated ? "/dashboard" : "/login"}
            className="text-sm text-indigo-400 hover:underline"
          >
            {isAuthenticated ? t("nav.dashboard") : t("landing.ctaSecondary")}
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-16 px-6 pb-20">
        <section className="space-y-6 pt-10 text-center">
          <p className="inline-block rounded-full border border-indigo-800 px-3 py-1 text-xs text-indigo-300">
            {t("landing.badge")}
          </p>
          <h1 className="text-4xl font-bold leading-tight sm:text-5xl">
            {t("landing.title")}
          </h1>
          <p className="mx-auto max-w-2xl text-neutral-400">
            {t("landing.subtitle")}
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link
              to="/register"
              className="rounded-md bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
            >
              {t("landing.ctaPrimary")}
            </Link>
            <Link
              to="/login"
              className="rounded-md border border-neutral-700 px-5 py-2.5 text-sm font-medium text-neutral-200 hover:bg-neutral-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
            >
              {t("landing.ctaSecondary")}
            </Link>
          </div>
        </section>

        <section className="grid gap-4 sm:grid-cols-3">
          {FEATURE_KEYS.map((key) => (
            <Card key={key} className="space-y-2">
              <h2 className="text-base font-semibold">
                {t(`landing.features.${key}Title`)}
              </h2>
              <p className="text-sm text-neutral-400">
                {t(`landing.features.${key}Body`)}
              </p>
            </Card>
          ))}
        </section>

        <section className="space-y-2 text-center">
          <h2 className="text-2xl font-semibold">{t("landing.securityTitle")}</h2>
          <p className="mx-auto max-w-2xl text-sm text-neutral-400">
            {t("landing.securityBody")}
          </p>
        </section>
      </main>

      <footer className="border-t border-neutral-900 py-6">
        <div className="mx-auto flex max-w-5xl justify-center gap-6 px-6 text-xs text-neutral-500">
          <Link to="/privacy" className="hover:text-neutral-300">
            {t("nav.privacy")}
          </Link>
          <Link to="/terms" className="hover:text-neutral-300">
            {t("nav.terms")}
          </Link>
        </div>
      </footer>
    </div>
  );
}
