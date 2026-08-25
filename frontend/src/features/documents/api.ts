import { apiClient } from "@/lib/api-client";
import type { Document } from "@/types/api";

export const documentApi = {
  async list(orgId: string): Promise<Document[]> {
    const { data } = await apiClient.get<Document[]>(`/documents/${orgId}`);
    return data;
  },

  async upload(orgId: string, file: File): Promise<Document> {
    const form = new FormData();
    form.append("file", file);
    const { data } = await apiClient.post<Document>(
      `/documents/${orgId}/upload`,
      form,
      { headers: { "Content-Type": "multipart/form-data" } },
    );
    return data;
  },

  async setFavorite(
    orgId: string,
    docId: string,
    isFavorite: boolean,
  ): Promise<Document> {
    const { data } = await apiClient.post<Document>(
      `/documents/${orgId}/${docId}/favorite`,
      { is_favorite: isFavorite },
    );
    return data;
  },

  async remove(orgId: string, docId: string): Promise<void> {
    await apiClient.delete(`/documents/${orgId}/${docId}`);
  },

  async downloadUrl(orgId: string, docId: string): Promise<string> {
    const { data } = await apiClient.get<{ url: string }>(
      `/documents/${orgId}/${docId}/download-url`,
    );
    return data.url;
  },
};

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
