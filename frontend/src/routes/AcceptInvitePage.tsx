import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { Card } from "@/components/ui/card";
import { orgApi } from "@/features/auth/api";
import { getApiErrorMessage } from "@/lib/api-error";
import { useAuthStore } from "@/stores/authStore";

export default function AcceptInvitePage() {
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const authenticated = useAuthStore((state) => state.isAuthenticated());
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: orgApi.acceptInvite,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["orgs"] });
      window.setTimeout(() => navigate("/dashboard"), 1_000);
    },
  });

  useEffect(() => {
    if (authenticated && token && mutation.isIdle) mutation.mutate(token);
  }, [authenticated, mutation, token]);

  const next = `/accept-invite?token=${encodeURIComponent(token)}`;
  const error = mutation.error
    ? getApiErrorMessage(mutation.error, "Davet kabul edilemedi.")
    : null;

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-md space-y-3 text-center">
        <h1 className="text-2xl font-bold">Ekip Daveti</h1>
        {!token && <p className="text-sm text-red-400">Davet token’ı eksik.</p>}
        {!authenticated && token && (
          <>
            <p className="text-sm text-neutral-400">
              Daveti kabul etmek için giriş yapın veya hesap oluşturun.
            </p>
            <div className="flex justify-center gap-3">
              <Link
                className="text-indigo-400 hover:underline"
                to={`/login?next=${encodeURIComponent(next)}`}
              >
                Giriş yap
              </Link>
              <Link
                className="text-indigo-400 hover:underline"
                to={`/register?next=${encodeURIComponent(next)}`}
              >
                Hesap oluştur
              </Link>
            </div>
          </>
        )}
        {mutation.isPending && <p className="text-sm">Davet kabul ediliyor…</p>}
        {mutation.isSuccess && (
          <p className="text-sm text-green-400">Davet kabul edildi.</p>
        )}
        {error && <p className="text-sm text-red-400">{error}</p>}
      </Card>
    </div>
  );
}
