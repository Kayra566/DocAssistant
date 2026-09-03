import { apiClient } from "@/lib/api-client";
import type { ModelInfo, ModelList } from "@/types/api";

export const modelApi = {
  async list(): Promise<ModelList> {
    const { data } = await apiClient.get<ModelList>("/models");
    return data;
  },

  async setActive(orgId: string, modelId: string): Promise<{ model_id: string }> {
    const { data } = await apiClient.put<{ model_id: string }>(
      `/models/${orgId}/active`,
      { model_id: modelId },
    );
    return data;
  },

  async importFile(orgId: string, filename: string): Promise<ModelInfo> {
    const { data } = await apiClient.post<ModelInfo>(`/models/${orgId}/import`, {
      filename,
    });
    return data;
  },
};

const SOURCE_LABELS: Record<string, string> = {
  ollama: "Ollama",
  file: "Klasörden",
  builtin: "Yerleşik",
};

export function sourceLabel(source: string): string {
  return SOURCE_LABELS[source] ?? source;
}

/** `file:qwen.gguf` kimliğinden dosya adını çıkarır. */
export function filenameOf(model: ModelInfo): string {
  return model.id.startsWith("file:") ? model.id.slice("file:".length) : "";
}
