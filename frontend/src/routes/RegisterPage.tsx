import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, Field } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { authApi } from "@/features/auth/api";
import { getApiErrorMessage } from "@/lib/api-error";
import { type RegisterInput, registerSchema } from "@/lib/validators";

export default function RegisterPage() {
  const [devToken, setDevToken] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterInput>({ resolver: zodResolver(registerSchema) });

  const mutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => setDevToken(data.dev_verification_token),
  });

  const errorMsg =
    mutation.error
      ? getApiErrorMessage(mutation.error, "Kayıt başarısız.")
      : null;

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm space-y-4">
        <h1 className="text-2xl font-bold">Hesap Oluştur</h1>
        {devToken ? (
          <div className="space-y-3">
            <p className="text-sm text-green-400">
              Kayıt başarılı! Email doğrulama gerekiyor.
            </p>
            <p className="break-all rounded bg-neutral-800 p-2 text-xs">
              Dev doğrulama token: <code>{devToken}</code>
            </p>
            <Link
              to={`/verify-email?token=${devToken}`}
              className="text-sm text-indigo-400 hover:underline"
            >
              Doğrulama sayfasına git →
            </Link>
          </div>
        ) : (
          <form
            className="space-y-3"
            onSubmit={handleSubmit((data) => mutation.mutate(data))}
          >
            <Field label="Ad Soyad" error={errors.full_name?.message}>
              <Input {...register("full_name")} />
            </Field>
            <Field label="Email" error={errors.email?.message}>
              <Input type="email" {...register("email")} />
            </Field>
            <Field label="Parola" error={errors.password?.message}>
              <Input type="password" {...register("password")} />
            </Field>
            <Field
              label="Organizasyon adı (opsiyonel)"
              error={errors.organization_name?.message}
            >
              <Input {...register("organization_name")} />
            </Field>
            {errorMsg && <p className="text-sm text-red-400">{errorMsg}</p>}
            <Button type="submit" className="w-full" disabled={mutation.isPending}>
              {mutation.isPending ? "Oluşturuluyor…" : "Kayıt Ol"}
            </Button>
          </form>
        )}
        <Link to="/login" className="block text-sm text-neutral-400 hover:text-indigo-400">
          Zaten hesabın var mı? Giriş yap
        </Link>
      </Card>
    </div>
  );
}
