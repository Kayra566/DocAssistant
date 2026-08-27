import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { aiApi } from "@/features/ai/api";
import type { Citation } from "@/types/api";

interface UiMessage {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
}

export default function ChatPage() {
  const { orgId = "", docId = "" } = useParams();
  const [question, setQuestion] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [messages, setMessages] = useState<UiMessage[]>([]);

  const chatMutation = useMutation({
    mutationFn: () =>
      aiApi.chat(orgId, {
        document_id: docId,
        question,
        conversation_id: conversationId,
      }),
    onSuccess: (res) => {
      setConversationId(res.conversation_id);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.answer, citations: res.citations },
      ]);
    },
  });

  const errorMsg =
    chatMutation.error instanceof AxiosError
      ? (chatMutation.error.response?.data?.detail ?? "Bir hata oluştu.")
      : null;

  function send() {
    if (!question.trim()) return;
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    chatMutation.mutate();
    setQuestion("");
  }

  return (
    <div className="mx-auto flex h-screen max-w-3xl flex-col gap-4 p-8">
      <Link
        to={`/organizations/${orgId}/documents`}
        className="text-sm text-indigo-400 hover:underline"
      >
        ← Dokümanlara dön
      </Link>
      <h1 className="text-2xl font-bold">Doküman Sohbeti</h1>

      <div className="flex-1 space-y-3 overflow-y-auto">
        {messages.length === 0 && (
          <p className="text-sm text-neutral-500">
            Doküman hakkında bir soru sorarak başlayın.
          </p>
        )}
        {messages.map((m, i) => (
          <Card
            key={i}
            className={m.role === "user" ? "bg-indigo-950/40" : "bg-neutral-900/60"}
          >
            <p className="mb-1 text-xs uppercase text-neutral-500">
              {m.role === "user" ? "Siz" : "Asistan"}
            </p>
            <div className="prose prose-invert max-w-none text-sm">
              <ReactMarkdown>{m.content}</ReactMarkdown>
            </div>
            {m.citations && m.citations.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {m.citations.map((c, ci) => (
                  <span
                    key={ci}
                    title={c.snippet}
                    className="rounded bg-neutral-800 px-2 py-0.5 text-xs text-neutral-400"
                  >
                    Sayfa {c.page} · {(c.score * 100).toFixed(0)}%
                  </span>
                ))}
              </div>
            )}
          </Card>
        ))}
        {chatMutation.isPending && (
          <p className="text-sm text-yellow-400">Yanıtlanıyor…</p>
        )}
      </div>

      {errorMsg && <p className="text-sm text-red-400">{errorMsg}</p>}

      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
      >
        <Input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Sorunuzu yazın…"
        />
        <Button type="submit" disabled={chatMutation.isPending}>
          Gönder
        </Button>
      </form>
    </div>
  );
}
