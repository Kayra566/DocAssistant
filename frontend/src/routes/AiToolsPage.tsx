import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, Field } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { aiToolsApi, jobResultText, quizQuestions } from "@/features/ai/tools-api";
import { documentApi } from "@/features/documents/api";
import type {
  AIJob,
  AIJobType,
  PromptPreset,
  QuizType,
  SummaryLevel,
} from "@/types/api";

const TOOLS: { key: AIJobType; label: string }[] = [
  { key: "summary", label: "Özet" },
  { key: "keypoints", label: "Kritik Bilgiler" },
  { key: "quiz", label: "Quiz" },
  { key: "translate", label: "Çeviri" },
  { key: "extract", label: "Veri Çıkarma" },
  { key: "compare", label: "Karşılaştır" },
];

const PRESETS: { key: PromptPreset; label: string }[] = [
  { key: "genel", label: "Genel" },
  { key: "hukuk", label: "Hukuk" },
  { key: "akademik", label: "Akademik" },
  { key: "is", label: "İş" },
];

const LEVELS: { key: SummaryLevel; label: string }[] = [
  { key: "short", label: "Kısa" },
  { key: "detailed", label: "Detaylı" },
  { key: "bullets", label: "Maddeli" },
  { key: "executive", label: "Yönetici" },
];

const QUIZ_TYPES: { key: QuizType; label: string }[] = [
  { key: "multiple_choice", label: "Çoktan seçmeli" },
  { key: "true_false", label: "Doğru/Yanlış" },
  { key: "open_ended", label: "Açık uçlu" },
];

const selectClass =
  "w-full rounded-md border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 focus:border-indigo-500 focus:outline-none";

function StringList({ title, items }: { title: string; items: unknown }) {
  const values = Array.isArray(items) ? items : [];
  return (
    <div>
      <p className="mb-1 text-xs uppercase text-neutral-500">{title}</p>
      {values.length === 0 ? (
        <p className="text-sm text-neutral-600">—</p>
      ) : (
        <ul className="list-inside list-disc text-sm text-neutral-300">
          {values.map((v, i) => (
            <li key={i}>{String(v)}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function QuizResult({ job }: { job: AIJob }) {
  const [revealed, setRevealed] = useState<Record<number, boolean>>({});
  const questions = quizQuestions(job);
  return (
    <div className="space-y-3">
      {questions.map((q, i) => (
        <div key={i} className="rounded-md border border-neutral-800 p-3">
          <p className="text-xs uppercase text-neutral-500">{q.type}</p>
          <p className="text-sm font-medium">{q.question}</p>
          {q.options?.length > 0 && (
            <ul className="mt-1 list-inside list-disc text-sm text-neutral-400">
              {q.options.map((o, oi) => (
                <li key={oi}>{o}</li>
              ))}
            </ul>
          )}
          <button
            className="mt-2 text-xs text-indigo-400 hover:underline"
            onClick={() => setRevealed((p) => ({ ...p, [i]: !p[i] }))}
          >
            {revealed[i] ? "Cevabı gizle" : "Cevabı göster"}
          </button>
          {revealed[i] && (
            <p className="mt-1 text-sm text-green-400">{q.answer}</p>
          )}
        </div>
      ))}
    </div>
  );
}

function ExtractResult({ job }: { job: AIJob }) {
  const columns = (job.result?.columns as string[]) ?? [];
  const records = (job.result?.records as Record<string, unknown>[]) ?? [];
  if (records.length === 0) return <p className="text-sm text-neutral-500">Kayıt yok.</p>;
  const headers = columns.length > 0 ? columns : Object.keys(records[0]);
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="text-xs uppercase text-neutral-500">
          <tr>
            {headers.map((h) => (
              <th key={h} className="border-b border-neutral-800 py-1 pr-4">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {records.map((row, i) => (
            <tr key={i}>
              {headers.map((h) => (
                <td key={h} className="border-b border-neutral-900 py-1 pr-4">
                  {String(row[h] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function JobResult({ job }: { job: AIJob }) {
  if (job.status === "failed") {
    return <p className="text-sm text-red-400">{job.error}</p>;
  }
  if (job.type === "quiz") return <QuizResult job={job} />;
  if (job.type === "extract") return <ExtractResult job={job} />;
  if (job.type === "keypoints") {
    return (
      <div className="grid gap-3 sm:grid-cols-2">
        <StringList title="Tarihler" items={job.result?.dates} />
        <StringList title="İsimler" items={job.result?.names} />
        <StringList title="Sayılar" items={job.result?.numbers} />
        <StringList title="Kararlar" items={job.result?.decisions} />
      </div>
    );
  }
  if (job.type === "compare") {
    return (
      <div className="space-y-3">
        <p className="text-sm text-neutral-300">{String(job.result?.summary ?? "")}</p>
        <div className="grid gap-3 sm:grid-cols-3">
          <StringList title="Yalnızca A" items={job.result?.only_in_a} />
          <StringList title="Yalnızca B" items={job.result?.only_in_b} />
          <StringList title="Ortak" items={job.result?.changed} />
        </div>
      </div>
    );
  }
  return (
    <div className="prose prose-invert max-w-none text-sm">
      <ReactMarkdown>{jobResultText(job)}</ReactMarkdown>
    </div>
  );
}

export default function AiToolsPage() {
  const { orgId = "", docId = "" } = useParams();
  const queryClient = useQueryClient();

  const [tool, setTool] = useState<AIJobType>("summary");
  const [preset, setPreset] = useState<PromptPreset>("genel");
  const [level, setLevel] = useState<SummaryLevel>("short");
  const [questionCount, setQuestionCount] = useState(5);
  const [quizTypes, setQuizTypes] = useState<QuizType[]>(["multiple_choice"]);
  const [targetLanguage, setTargetLanguage] = useState("İngilizce");
  const [schemaHint, setSchemaHint] = useState("");
  const [otherDocId, setOtherDocId] = useState("");
  const [job, setJob] = useState<AIJob | null>(null);

  const docsQuery = useQuery({
    queryKey: ["documents", orgId],
    queryFn: () => documentApi.list(orgId),
  });

  const jobsQuery = useQuery({
    queryKey: ["ai-jobs", orgId, docId],
    queryFn: () => aiToolsApi.jobs(orgId, { documentId: docId }),
  });

  const runMutation = useMutation({
    mutationFn: (): Promise<AIJob> => {
      switch (tool) {
        case "keypoints":
          return aiToolsApi.keypoints(orgId, docId, preset);
        case "quiz":
          return aiToolsApi.quiz(orgId, docId, questionCount, quizTypes, preset);
        case "translate":
          return aiToolsApi.translate(orgId, docId, targetLanguage, preset);
        case "extract":
          return aiToolsApi.extract(orgId, docId, schemaHint, preset);
        case "compare":
          return aiToolsApi.compare(orgId, docId, otherDocId, preset);
        default:
          return aiToolsApi.summary(orgId, docId, level, preset);
      }
    },
    onSuccess: (result) => {
      setJob(result);
      queryClient.invalidateQueries({ queryKey: ["ai-jobs", orgId, docId] });
    },
  });

  const errorMsg =
    runMutation.error instanceof AxiosError
      ? (runMutation.error.response?.data?.detail ?? "Bir hata oluştu.")
      : null;

  const otherDocs = (docsQuery.data ?? []).filter(
    (d) => d.id !== docId && d.status === "ready",
  );
  const canRun = tool !== "compare" || Boolean(otherDocId);

  function toggleQuizType(type: QuizType) {
    setQuizTypes((prev) => {
      if (!prev.includes(type)) return [...prev, type];
      // En az bir tip seçili kalmalı.
      return prev.length === 1 ? prev : prev.filter((t) => t !== type);
    });
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-8">
      <Link
        to={`/organizations/${orgId}/documents`}
        className="text-sm text-indigo-400 hover:underline"
      >
        ← Dokümanlara dön
      </Link>
      <h1 className="text-3xl font-bold">AI Araçları</h1>

      <Card className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {TOOLS.map((t) => (
            <Button
              key={t.key}
              variant={tool === t.key ? "primary" : "ghost"}
              className="px-3 py-1 text-xs"
              onClick={() => {
                setTool(t.key);
                setJob(null);
              }}
            >
              {t.label}
            </Button>
          ))}
        </div>

        <Field label="Prompt şablonu">
          <select
            className={selectClass}
            value={preset}
            onChange={(e) => setPreset(e.target.value as PromptPreset)}
          >
            {PRESETS.map((p) => (
              <option key={p.key} value={p.key}>
                {p.label}
              </option>
            ))}
          </select>
        </Field>

        {tool === "summary" && (
          <Field label="Özet seviyesi">
            <select
              className={selectClass}
              value={level}
              onChange={(e) => setLevel(e.target.value as SummaryLevel)}
            >
              {LEVELS.map((l) => (
                <option key={l.key} value={l.key}>
                  {l.label}
                </option>
              ))}
            </select>
          </Field>
        )}

        {tool === "quiz" && (
          <>
            <Field label="Soru sayısı">
              <Input
                type="number"
                min={1}
                max={20}
                value={questionCount}
                onChange={(e) => setQuestionCount(Number(e.target.value))}
              />
            </Field>
            <div className="flex flex-wrap gap-2">
              {QUIZ_TYPES.map((t) => (
                <Button
                  key={t.key}
                  variant={quizTypes.includes(t.key) ? "primary" : "ghost"}
                  className="px-3 py-1 text-xs"
                  onClick={() => toggleQuizType(t.key)}
                >
                  {t.label}
                </Button>
              ))}
            </div>
          </>
        )}

        {tool === "translate" && (
          <Field label="Hedef dil">
            <Input
              value={targetLanguage}
              onChange={(e) => setTargetLanguage(e.target.value)}
              placeholder="İngilizce"
            />
          </Field>
        )}

        {tool === "extract" && (
          <Field label="İstenen alanlar (opsiyonel)">
            <Input
              value={schemaHint}
              onChange={(e) => setSchemaHint(e.target.value)}
              placeholder="tarih, tutar, taraf"
            />
          </Field>
        )}

        {tool === "compare" && (
          <Field label="Karşılaştırılacak doküman">
            <select
              className={selectClass}
              value={otherDocId}
              onChange={(e) => setOtherDocId(e.target.value)}
            >
              <option value="">Seçiniz…</option>
              {otherDocs.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename}
                </option>
              ))}
            </select>
          </Field>
        )}

        <Button
          onClick={() => runMutation.mutate()}
          disabled={runMutation.isPending || !canRun}
        >
          {runMutation.isPending ? "Çalışıyor…" : "Çalıştır"}
        </Button>
        {errorMsg && <p className="text-sm text-red-400">{errorMsg}</p>}
      </Card>

      {job && (
        <Card className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Sonuç</h2>
            <span className="text-xs text-neutral-500">
              {job.tokens_used} token{job.cache_hit ? " · önbellekten" : ""}
            </span>
          </div>
          <JobResult job={job} />
        </Card>
      )}

      <Card className="space-y-2">
        <h2 className="text-lg font-semibold">Geçmiş İşlemler</h2>
        {jobsQuery.data?.length === 0 && (
          <p className="text-sm text-neutral-500">Henüz AI işlemi yok.</p>
        )}
        <ul className="space-y-1">
          {jobsQuery.data
            ?.filter((j) => j.type !== "chat")
            .map((j) => (
              <li key={j.id}>
                <button
                  onClick={() => {
                    setTool(j.type);
                    setJob(j);
                  }}
                  className="w-full rounded-md border border-neutral-800 px-3 py-2 text-left text-sm hover:border-neutral-600"
                >
                  <span className="font-medium">{j.type}</span>
                  <span className="ml-2 text-xs text-neutral-500">
                    {new Date(j.created_at).toLocaleString("tr-TR")} · {j.status}
                  </span>
                </button>
              </li>
            ))}
        </ul>
      </Card>
    </div>
  );
}
