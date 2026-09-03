import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, Field } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { authApi } from "@/features/auth/api";
import { getApiErrorMessage } from "@/lib/api-error";
import { type LoginInput, loginSchema } from "@/lib/validators";
import { useAuthStore } from "@/stores/authStore";

export default function LoginPage() {
  const navigate = useNavigate();
  const setTokens = useAuthStore((s) => s.setTokens);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginInput>({ resolver: zodResolver(loginSchema) });

  const mutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (tokens) => {
      setTokens(tokens.access_token, tokens.refresh_token);
      navigate("/dashboard");
    },
  });

  const errorMsg = mutation.error
    ? getApiErrorMessage(mutation.error, "Giriş başarısız.")
    : null;

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm space-y-4">
        <h1 className="text-2xl font-bold">Giriş Yap</h1>
        <form
          className="space-y-3"
          onSubmit={handleSubmit((data) => mutation.mutate(data))}
        >
          <Field label="Email" error={errors.email?.message}>
            <Input type="email" {...register("email")} />
          </Field>
          <Field label="Parola" error={errors.password?.message}>
            <Input type="password" {...register("password")} />
          </Field>
          <Field label="2FA Kodu (varsa)">
            <Input inputMode="numeric" {...register("totp_code")} />
          </Field>
          {errorMsg && <p className="text-sm text-red-400">{errorMsg}</p>}
          <Button type="submit" className="w-full" disabled={mutation.isPending}>
            {mutation.isPending ? "Giriş yapılıyor…" : "Giriş Yap"}
          </Button>
        </form>
        <div className="flex justify-between text-sm text-neutral-400">
          <Link to="/register" className="hover:text-indigo-400">
            Hesap oluştur
          </Link>
          <Link to="/forgot-password" className="hover:text-indigo-400">
            Parolamı unuttum
          </Link>
        </div>
      </Card>
    </div>
  );
}
