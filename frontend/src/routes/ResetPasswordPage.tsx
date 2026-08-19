import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, Field } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { authApi } from "@/features/auth/api";
import { type ResetInput, resetSchema } from "@/lib/validators";

export default function ResetPasswordPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetInput>({
    resolver: zodResolver(resetSchema),
    defaultValues: { token: params.get("token") ?? "" },
  });

  const mutation = useMutation({
    mutationFn: (data: ResetInput) =>
      authApi.resetPassword(data.token, data.new_password),
    onSuccess: () => setTimeout(() => navigate("/login"), 1500),
  });

  const errorMsg =
    mutation.error instanceof AxiosError
      ? (mutation.error.response?.data?.detail ?? "Sıfırlama başarısız.")
      : null;

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm space-y-4">
        <h1 className="text-2xl font-bold">Yeni Parola</h1>
        {mutation.isSuccess ? (
          <p className="text-sm text-green-400">
            Parola güncellendi. Giriş sayfasına yönlendiriliyorsunuz…
          </p>
        ) : (
          <form
            className="space-y-3"
            onSubmit={handleSubmit((data) => mutation.mutate(data))}
          >
            <Field label="Token" error={errors.token?.message}>
              <Input {...register("token")} />
            </Field>
            <Field label="Yeni Parola" error={errors.new_password?.message}>
              <Input type="password" {...register("new_password")} />
            </Field>
            {errorMsg && <p className="text-sm text-red-400">{errorMsg}</p>}
            <Button type="submit" className="w-full" disabled={mutation.isPending}>
              Parolayı Güncelle
            </Button>
          </form>
        )}
        <Link to="/login" className="block text-sm text-neutral-400 hover:text-indigo-400">
          Giriş sayfasına dön
        </Link>
      </Card>
    </div>
  );
}
