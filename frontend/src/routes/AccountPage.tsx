import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, Field } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { gdprApi } from "@/features/system/api";
import { useAuthStore } from "@/stores/authStore";

export default function AccountPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const clear = useAuthStore((state) => state.clear);

  const [password, setPassword] = useState("");
  const [confirmed, setConfirmed] = useState(false);

  const exportMutation = useMutation({ mutationFn: gdprApi.exportData });

  const deleteMutation = useMutation({
    mutationFn: () => gdprApi.deleteAccount(password),
    onSuccess: () => {
      clear();
      navigate("/");
    },
  });

  const errorMsg =
    deleteMutation.error instanceof AxiosError
      ? (deleteMutation.error.response?.data?.detail ?? "İşlem başarısız.")
      : null;

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-8">
      <Link to="/dashboard" className="text-sm text-indigo-400 hover:underline">
        {t("common.backToDashboard")}
      </Link>
      <h1 className="text-3xl font-bold">{t("account.title")}</h1>

      <Card className="space-y-3">
        <h2 className="text-lg font-semibold">{t("account.exportTitle")}</h2>
        <p className="text-sm text-neutral-400">{t("account.exportBody")}</p>
        <Button
          onClick={() => exportMutation.mutate()}
          disabled={exportMutation.isPending}
        >
          {t("account.exportAction")}
        </Button>
      </Card>

      <Card className="space-y-3 border-red-900">
        <h2 className="text-lg font-semibold text-red-400">
          {t("account.deleteTitle")}
        </h2>
        <p className="text-sm text-neutral-400">{t("account.deleteBody")}</p>

        <Field label={t("account.passwordLabel")}>
          <Input
            type="password"
            value={password}
            autoComplete="current-password"
            onChange={(event) => setPassword(event.target.value)}
          />
        </Field>

        <label className="flex items-center gap-2 text-sm text-neutral-300">
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(event) => setConfirmed(event.target.checked)}
            className="h-4 w-4 rounded border-neutral-700 bg-neutral-900"
          />
          {t("account.confirmLabel")}
        </label>

        {errorMsg && <p className="text-sm text-red-400">{errorMsg}</p>}

        <Button
          variant="danger"
          disabled={!password || !confirmed || deleteMutation.isPending}
          onClick={() => deleteMutation.mutate()}
        >
          {t("account.deleteConfirm")}
        </Button>
      </Card>
    </div>
  );
}
