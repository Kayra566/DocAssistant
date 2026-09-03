import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { shareApi, shareExpired } from "@/features/sharing/api";
import { getApiErrorMessage } from "@/lib/api-error";
import type { SharePermission } from "@/types/api";

const selectClass =
  "w-full rounded-md border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 focus:border-indigo-500 focus:outline-none";

export function ShareDialog({
  orgId,
  documentId,
  filename,
  onClose,
}: {
  orgId: string;
  documentId: string;
  filename: string;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [permission, setPermission] = useState<SharePermission>("view");
  const [email, setEmail] = useState("");
  const [expiresInHours, setExpiresInHours] = useState(168);
  const [createdUrl, setCreatedUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const linksQuery = useQuery({
    queryKey: ["shares", orgId, documentId],
    queryFn: () => shareApi.list(orgId, documentId),
  });

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["shares", orgId, documentId] });

  const createMutation = useMutation({
    mutationFn: () =>
      shareApi.create(orgId, {
        document_id: documentId,
        permission,
        email: email.trim() || null,
        expires_in_hours: expiresInHours,
      }),
    onSuccess: (link) => {
      setCreatedUrl(link.url);
      setCopied(false);
      invalidate();
    },
  });

  const revokeMutation = useMutation({
    mutationFn: (shareId: string) => shareApi.revoke(orgId, shareId),
    onSuccess: invalidate,
  });

  const errorMsg =
    createMutation.error
      ? getApiErrorMessage(createMutation.error, "Bağlantı oluşturulamadı.")
      : null;

  async function copyUrl() {
    if (!createdUrl) return;
    await navigator.clipboard.writeText(createdUrl);
    setCopied(true);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
    >
      <div
        className="max-h-[90vh] w-full max-w-lg space-y-4 overflow-y-auto rounded-xl border border-neutral-800 bg-neutral-900 p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between">
          <div className="min-w-0">
            <h2 className="text-lg font-semibold">Dokümanı paylaş</h2>
            <p className="truncate text-xs text-neutral-500">{filename}</p>
          </div>
          <Button variant="ghost" className="px-2 py-1 text-xs" onClick={onClose}>
            Kapat
          </Button>
        </div>

        <Field label="İzin">
          <select
            className={selectClass}
            value={permission}
            onChange={(e) => setPermission(e.target.value as SharePermission)}
          >
            <option value="view">Yalnızca görüntüleme</option>
            <option value="download">Görüntüleme + indirme</option>
          </select>
        </Field>

        <Field label="E-posta ile sınırla (opsiyonel)">
          <Input
            type="email"
            value={email}
            placeholder="ornek@firma.com"
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>

        <Field label="Geçerlilik (saat)">
          <Input
            type="number"
            min={1}
            max={720}
            value={expiresInHours}
            onChange={(e) => setExpiresInHours(Number(e.target.value))}
          />
        </Field>

        <Button
          onClick={() => createMutation.mutate()}
          disabled={createMutation.isPending}
        >
          {createMutation.isPending ? "Oluşturuluyor…" : "Bağlantı oluştur"}
        </Button>
        {errorMsg && <p className="text-sm text-red-400">{errorMsg}</p>}

        {createdUrl && (
          <div className="space-y-2 rounded-md border border-indigo-800 bg-indigo-950/40 p-3">
            <p className="text-xs text-neutral-400">
              Bağlantı yalnızca şimdi gösterilir, kopyalayın:
            </p>
            <p className="break-all text-xs text-indigo-300">{createdUrl}</p>
            <Button variant="ghost" className="px-2 py-1 text-xs" onClick={copyUrl}>
              {copied ? "Kopyalandı" : "Kopyala"}
            </Button>
          </div>
        )}

        <div className="space-y-2">
          <h3 className="text-sm font-semibold">Mevcut bağlantılar</h3>
          {linksQuery.data?.length === 0 && (
            <p className="text-xs text-neutral-500">Henüz paylaşım yok.</p>
          )}
          <ul className="space-y-2">
            {linksQuery.data?.map((link) => (
              <li
                key={link.id}
                className="flex items-center justify-between rounded-md border border-neutral-800 px-3 py-2 text-xs"
              >
                <div className="min-w-0">
                  <p className="text-neutral-300">
                    {link.permission === "download" ? "İndirilebilir" : "Görüntüleme"}
                    {link.email && ` · ${link.email}`}
                  </p>
                  <p className="text-neutral-500">
                    {link.view_count} görüntüleme ·{" "}
                    {shareExpired(link)
                      ? "pasif"
                      : `${new Date(link.expires_at).toLocaleString("tr-TR")} sonuna kadar`}
                  </p>
                </div>
                {!link.revoked && (
                  <Button
                    variant="danger"
                    className="px-2 py-1 text-xs"
                    onClick={() => revokeMutation.mutate(link.id)}
                  >
                    İptal
                  </Button>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
