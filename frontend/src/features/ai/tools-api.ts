import { apiClient } from "@/lib/api-client";
import type {
  AIJob,
  AIJobType,
  PromptPreset,
  PromptPresets,
  QuizQuestion,
  QuizType,
  SummaryLevel,
} from "@/types/api";

async function post(orgId: string, path: string, payload: object) {
  const { data } = await apiClient.post<AIJob>(`/ai/${orgId}/${path}`, payload);
  return data;
}

export const aiToolsApi = {
  presets: async (): Promise<PromptPresets> => {
    const { data } = await apiClient.get<PromptPresets>("/ai/prompt-presets");
    return data;
  },

  summary: (
    orgId: string,
    documentId: string,
    level: SummaryLevel,
    preset: PromptPreset,
  ) => post(orgId, "summary", { document_id: documentId, level, preset }),

  keypoints: (orgId: string, documentId: string, preset: PromptPreset) =>
    post(orgId, "keypoints", { document_id: documentId, preset }),

  quiz: (
    orgId: string,
    documentId: string,
    questionCount: number,
    questionTypes: QuizType[],
    preset: PromptPreset,
  ) =>
    post(orgId, "quiz", {
      document_id: documentId,
      question_count: questionCount,
      question_types: questionTypes,
      preset,
    }),

  translate: (
    orgId: string,
    documentId: string,
    targetLanguage: string,
    preset: PromptPreset,
  ) =>
    post(orgId, "translate", {
      document_id: documentId,
      target_language: targetLanguage,
      preset,
    }),

  extract: (
    orgId: string,
    documentId: string,
    schemaHint: string | null,
    preset: PromptPreset,
  ) =>
    post(orgId, "extract", {
      document_id: documentId,
      schema_hint: schemaHint || null,
      preset,
    }),

  compare: (
    orgId: string,
    documentId: string,
    otherDocumentId: string,
    preset: PromptPreset,
  ) =>
    post(orgId, "compare", {
      document_id: documentId,
      other_document_id: otherDocumentId,
      preset,
    }),

  jobs: async (
    orgId: string,
    params: { documentId?: string; type?: AIJobType } = {},
  ): Promise<AIJob[]> => {
    const { data } = await apiClient.get<AIJob[]>(`/ai/${orgId}/jobs`, {
      params: { document_id: params.documentId, type: params.type },
    });
    return data;
  },
};

/** AIJob.result içeriğini UI'da göstermeye uygun biçime indirger. */
export function jobResultText(job: AIJob): string {
  const result = job.result;
  if (!result) return "";
  if (typeof result.text === "string") return result.text;
  return JSON.stringify(result, null, 2);
}

export function quizQuestions(job: AIJob): QuizQuestion[] {
  const questions = job.result?.questions;
  return Array.isArray(questions) ? (questions as QuizQuestion[]) : [];
}
