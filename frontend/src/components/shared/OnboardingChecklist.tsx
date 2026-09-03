import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const STORAGE_KEY = "docassistant-onboarding-dismissed";

export function OnboardingChecklist({
  orgId,
  hasDocuments,
  hasAiJobs,
}: {
  orgId: string;
  hasDocuments: boolean;
  hasAiJobs: boolean;
}) {
  const { t } = useTranslation();
  const [dismissed, setDismissed] = useState(
    () => localStorage.getItem(STORAGE_KEY) === "true",
  );

  const steps = [
    {
      key: "step1",
      done: hasDocuments,
      to: `/organizations/${orgId}/documents`,
    },
    { key: "step2", done: hasAiJobs, to: `/organizations/${orgId}/documents` },
    { key: "step3", done: hasAiJobs, to: `/organizations/${orgId}/documents` },
  ];

  if (dismissed || steps.every((step) => step.done)) return null;

  function dismiss() {
    localStorage.setItem(STORAGE_KEY, "true");
    setDismissed(true);
  }

  return (
    <Card className="space-y-3 border-indigo-900 bg-indigo-950/20">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{t("onboarding.title")}</h2>
        <Button variant="ghost" className="px-2 py-1 text-xs" onClick={dismiss}>
          {t("onboarding.dismiss")}
        </Button>
      </div>
      <ol className="space-y-2">
        {steps.map((step, index) => (
          <li key={step.key} className="flex items-start gap-3">
            <span
              aria-hidden="true"
              className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] ${
                step.done
                  ? "bg-green-600 text-white"
                  : "border border-neutral-700 text-neutral-400"
              }`}
            >
              {step.done ? "✓" : index + 1}
            </span>
            <div>
              <Link
                to={step.to}
                className="text-sm font-medium text-indigo-300 hover:underline"
              >
                {t(`onboarding.${step.key}`)}
              </Link>
              <p className="text-xs text-neutral-500">
                {t(`onboarding.${step.key}Body`)}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </Card>
  );
}
