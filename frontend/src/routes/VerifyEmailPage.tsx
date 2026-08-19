import { useMutation } from "@tanstack/react-query";
import { useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { Card } from "@/components/ui/card";
import { authApi } from "@/features/auth/api";

export default function VerifyEmailPage() {
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";

  const mutation = useMutation({ mutationFn: authApi.verifyEmail });

  useEffect(() => {
    if (token) mutation.mutate(token);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm space-y-3 text-center">
        <h1 className="text-2xl font-bold">Email Doğrulama</h1>
        {!token && <p className="text-sm text-red-400">Token bulunamadı.</p>}
        {mutation.isPending && <p className="text-sm text-neutral-400">Doğrulanıyor…</p>}
        {mutation.isSuccess && (
          <p className="text-sm text-green-400">Email başarıyla doğrulandı ✓</p>
        )}
        {mutation.isError && (
          <p className="text-sm text-red-400">Doğrulama başarısız veya süresi dolmuş.</p>
        )}
        <Link to="/login" className="block text-sm text-indigo-400 hover:underline">
          Giriş sayfasına dön
        </Link>
      </Card>
    </div>
  );
}
