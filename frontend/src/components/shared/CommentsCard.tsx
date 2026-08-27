import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { commentApi } from "@/features/sharing/api";
import { useAuthStore } from "@/stores/authStore";

export function CommentsCard({
  orgId,
  docId,
}: {
  orgId: string;
  docId: string;
}) {
  const queryClient = useQueryClient();
  const currentUser = useAuthStore((state) => state.user);
  const [content, setContent] = useState("");

  const commentsQuery = useQuery({
    queryKey: ["comments", orgId, docId],
    queryFn: () => commentApi.list(orgId, docId),
  });

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["comments", orgId, docId] });

  const createMutation = useMutation({
    mutationFn: () => commentApi.create(orgId, docId, content.trim()),
    onSuccess: () => {
      setContent("");
      invalidate();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (commentId: string) => commentApi.remove(orgId, docId, commentId),
    onSuccess: invalidate,
  });

  return (
    <Card className="space-y-3">
      <h2 className="text-lg font-semibold">Notlar</h2>

      {commentsQuery.data?.length === 0 && (
        <p className="text-sm text-neutral-500">Henüz not yok.</p>
      )}
      <ul className="space-y-2">
        {commentsQuery.data?.map((comment) => (
          <li
            key={comment.id}
            className="flex items-start justify-between gap-3 rounded-md border border-neutral-800 px-3 py-2"
          >
            <div className="min-w-0">
              <p className="text-sm text-neutral-200">{comment.content}</p>
              <p className="text-xs text-neutral-500">
                {comment.author_email ?? "Bilinmiyor"} ·{" "}
                {new Date(comment.created_at).toLocaleString("tr-TR")}
                {comment.page !== null && ` · sayfa ${comment.page}`}
              </p>
            </div>
            {comment.author_email === currentUser?.email && (
              <Button
                variant="ghost"
                className="shrink-0 px-2 py-1 text-xs text-red-400"
                onClick={() => deleteMutation.mutate(comment.id)}
              >
                Sil
              </Button>
            )}
          </li>
        ))}
      </ul>

      <textarea
        className="w-full rounded-md border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 focus:border-indigo-500 focus:outline-none"
        rows={2}
        placeholder="Bu doküman hakkında not ekleyin…"
        value={content}
        onChange={(e) => setContent(e.target.value)}
      />
      <Button
        onClick={() => createMutation.mutate()}
        disabled={!content.trim() || createMutation.isPending}
      >
        Not ekle
      </Button>
    </Card>
  );
}
