import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";

const STORAGE_KEY = "docassistant-cookie-consent";

export function CookieConsent() {
  const { t } = useTranslation();
  const [decided, setDecided] = useState(
    () => localStorage.getItem(STORAGE_KEY) !== null,
  );

  if (decided) return null;

  function decide(value: "accepted" | "rejected") {
    localStorage.setItem(STORAGE_KEY, value);
    setDecided(true);
  }

  return (
    <div
      role="region"
      aria-label={t("cookies.policy")}
      className="fixed inset-x-0 bottom-0 z-50 border-t border-neutral-800 bg-neutral-950/95 p-4"
    >
      <div className="mx-auto flex max-w-4xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-neutral-300">
          {t("cookies.message")}{" "}
          <Link to="/privacy" className="text-indigo-400 hover:underline">
            {t("cookies.policy")}
          </Link>
        </p>
        <div className="flex shrink-0 gap-2">
          <Button
            variant="ghost"
            className="border border-neutral-700"
            onClick={() => decide("rejected")}
          >
            {t("cookies.reject")}
          </Button>
          <Button onClick={() => decide("accepted")}>{t("cookies.accept")}</Button>
        </div>
      </div>
    </div>
  );
}
