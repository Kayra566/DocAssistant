import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, Field } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { authApi } from "@/features/auth/api";
import { type ForgotInput, forgotSchema } from "@/lib/validators";

export default function ForgotPasswordPage() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotInput>({ resolver: zodResolver(forgotSchema) });

  const mutation = useMutation({
    mutationFn: (data: ForgotInput) => authApi.forgotPassword(data.email),
  });

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm space-y-4">
        <h1 className="text-2xl font-bold">Parola Sıfırlama</h1>
        {mutation.isSuccess ? (
          <div className="space-y-3">
            <p className="text-sm text-green-400">{mutation.data.message}</p>
            {mutation.data.dev_token && (
              <Link
                to={`/reset-password?token=${mutation.data.dev_token}`}
                className="break-all text-xs text-indigo-400 hover:underline"
              >
                Dev: sıfırlama sayfasına git →
              </Link>
            )}
          </div>
        ) : (
          <form
            className="space-y-3"
            onSubmit={handleSubmit((data) => mutation.mutate(data))}
          >
            <Field label="Email" error={errors.email?.message}>
              <Input type="email" {...register("email")} />
            </Field>
            <Button type="submit" className="w-full" disabled={mutation.isPending}>
              Sıfırlama bağlantısı gönder
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
