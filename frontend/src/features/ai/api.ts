import { apiClient } from "@/lib/api-client";
import type { ChatMessage, ChatResponse, Usage } from "@/types/api";

export const aiApi = {
  async chat(
    orgId: string,
    payload: {
      document_id: string;
      question: string;
      conversation_id?: string;
    },
  ): Promise<ChatResponse> {
    const { data } = await apiClient.post<ChatResponse>(
      `/ai/${orgId}/chat`,
      payload,
    );
    return data;
  },

  async messages(orgId: string, conversationId: string): Promise<ChatMessage[]> {
    const { data } = await apiClient.get<ChatMessage[]>(
      `/ai/${orgId}/conversations/${conversationId}/messages`,
    );
    return data;
  },

  async usage(orgId: string): Promise<Usage> {
    const { data } = await apiClient.get<Usage>(`/ai/${orgId}/usage`);
    return data;
  },
};
