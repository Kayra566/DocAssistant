import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, Field } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { orgApi } from "@/features/auth/api";
import type { Role } from "@/types/api";

export default function TeamPage() {
  const { orgId = "" } = useParams();
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Role>("member");

  const membersQuery = useQuery({
    queryKey: ["members", orgId],
    queryFn: () => orgApi.members(orgId),
  });

  const inviteMutation = useMutation({
    mutationFn: () => orgApi.invite(orgId, email, role),
    onSuccess: () => {
      setEmail("");
      queryClient.invalidateQueries({ queryKey: ["members", orgId] });
    },
  });

  const errorMsg =
    inviteMutation.error instanceof AxiosError
      ? (inviteMutation.error.response?.data?.detail ?? "Davet başarısız.")
      : null;

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-8">
      <Link to="/dashboard" className="text-sm text-indigo-400 hover:underline">
        ← Panele dön
      </Link>
      <h1 className="text-3xl font-bold">Ekip Yönetimi</h1>

      <Card className="space-y-3">
        <h2 className="text-lg font-semibold">Üyeler</h2>
        {membersQuery.isLoading && (
          <p className="text-sm text-neutral-400">Yükleniyor…</p>
        )}
        <ul className="space-y-2">
          {membersQuery.data?.map((m) => (
            <li
              key={m.user_id}
              className="flex items-center justify-between rounded-md border border-neutral-800 px-3 py-2 text-sm"
            >
              <span>{m.full_name ?? m.email}</span>
              <span className="text-xs uppercase text-neutral-500">{m.role}</span>
            </li>
          ))}
        </ul>
      </Card>

      <Card className="space-y-3">
        <h2 className="text-lg font-semibold">Üye Davet Et</h2>
        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            inviteMutation.mutate();
          }}
        >
          <Field label="Email">
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </Field>
          <Field label="Rol">
            <select
              className="w-full rounded-md border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm"
              value={role}
              onChange={(e) => setRole(e.target.value as Role)}
            >
              <option value="viewer">Viewer</option>
              <option value="member">Member</option>
              <option value="admin">Admin</option>
            </select>
          </Field>
          {errorMsg && <p className="text-sm text-red-400">{errorMsg}</p>}
          {inviteMutation.isSuccess && (
            <p className="text-sm text-green-400">Davet oluşturuldu.</p>
          )}
          <Button type="submit" disabled={inviteMutation.isPending}>
            Davet Gönder
          </Button>
        </form>
      </Card>
    </div>
  );
}
