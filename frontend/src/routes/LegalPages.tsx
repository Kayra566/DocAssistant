import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Card } from "@/components/ui/card";

/** Gizlilik ve kullanım koşulları sayfalarını aynı düzenle üretir. */
export function LegalPage({
  namespace,
  sections,
}: {
  namespace: "privacy" | "terms";
  sections: string[];
}) {
  const { t } = useTranslation();

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-8">
      <Link to="/" className="text-sm text-indigo-400 hover:underline">
        ← DocAssistant
      </Link>
      <div>
        <h1 className="text-3xl font-bold">{t(`${namespace}.title`)}</h1>
        <p className="text-xs text-neutral-500">{t(`${namespace}.updated`)}</p>
      </div>

      <Card className="space-y-5">
        {sections.map((section) => (
          <section key={section} className="space-y-1">
            <h2 className="text-base font-semibold">
              {t(`${namespace}.${section}Title`)}
            </h2>
            <p className="text-sm text-neutral-400">
              {t(`${namespace}.${section}Body`)}
            </p>
          </section>
        ))}
      </Card>
    </div>
  );
}

export function PrivacyPage() {
  return (
    <LegalPage
      namespace="privacy"
      sections={["controller", "data", "rights", "retention", "contact"]}
    />
  );
}

export function TermsPage() {
  return (
    <LegalPage
      namespace="terms"
      sections={["service", "account", "content", "billing", "liability"]}
    />
  );
}
