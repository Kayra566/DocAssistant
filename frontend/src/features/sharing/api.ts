import axios from "axios";

import { apiClient } from "@/lib/api-client";
import type {
  DocumentComment,
  ShareLink,
  ShareLinkCreated,
  SharePermission,
  SharedDocument,
} from "@/types/api";

/** Public paylaşım uçları oturum gerektirmez; auth interceptor'ından uzak tutulur. */
const publicClient = axios.create({ baseURL: apiClient.defaults.baseURL });

export const shareApi = {
  async create(
    orgId: string,
    payload: {
      document_id: string;
      permission: SharePermission;
      email?: string | null;
      expires_in_hours?: number | null;
    },
  ): Promise<ShareLinkCreated> {
    const { data } = await apiClient.post<ShareLinkCreated>(
      `/shares/${orgId}`,
      payload,
    );
    return data;
  },

  async list(orgId: string, documentId?: string): Promise<ShareLink[]> {
    const { data } = await apiClient.get<ShareLink[]>(`/shares/${orgId}`, {
      params: documentId ? { document_id: documentId } : undefined,
    });
    return data;
  },

  async revoke(orgId: string, shareId: string): Promise<ShareLink> {
    const { data } = await apiClient.delete<ShareLink>(
      `/shares/${orgId}/${shareId}`,
    );
    return data;
  },

  async publicInfo(token: string, email?: string): Promise<SharedDocument> {
    const { data } = await publicClient.get<SharedDocument>(
      `/shares/public/${token}`,
      { params: email ? { email } : undefined },
    );
    return data;
  },

  publicDownloadUrl(token: string, email?: string): string {
    const base = `${apiClient.defaults.baseURL}/shares/public/${token}/download`;
    return email ? `${base}?email=${encodeURIComponent(email)}` : base;
  },
};

export const commentApi = {
  async list(orgId: string, docId: string): Promise<DocumentComment[]> {
    const { data } = await apiClient.get<DocumentComment[]>(
      `/documents/${orgId}/${docId}/comments`,
    );
    return data;
  },

  async create(
    orgId: string,
    docId: string,
    content: string,
    page?: number | null,
  ): Promise<DocumentComment> {
    const { data } = await apiClient.post<DocumentComment>(
      `/documents/${orgId}/${docId}/comments`,
      { content, page: page ?? null },
    );
    return data;
  },

  async remove(orgId: string, docId: string, commentId: string): Promise<void> {
    await apiClient.delete(`/documents/${orgId}/${docId}/comments/${commentId}`);
  },
};

export function shareExpired(link: ShareLink): boolean {
  return link.revoked || new Date(link.expires_at) < new Date();
}
