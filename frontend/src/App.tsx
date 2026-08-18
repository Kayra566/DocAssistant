import { useQuery } from "@tanstack/react-query";

import { apiClient } from "./lib/api-client";

function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const { data } = await apiClient.get<{ status: string }>("/health");
      return data;
    },
  });
}

export default function App() {
  const { data, isLoading, isError } = useHealth();

  const status = isLoading
    ? "kontrol ediliyor…"
    : isError
      ? "backend'e ulaşılamadı"
      : (data?.status ?? "bilinmiyor");

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-8">
      <h1 className="text-4xl font-bold">DocAssistant</h1>
      <p className="text-neutral-400">AI destekli doküman asistanı — Faz 0 iskeleti</p>
      <div className="rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-2 text-sm">
        Backend durumu: <span className="font-mono">{status}</span>
      </div>
    </main>
  );
}
