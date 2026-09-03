import { apiClient } from "@/lib/api-client";
import type { AppNotification, FeatureFlags } from "@/types/api";

export const notificationApi = {
  async list(): Promise<AppNotification[]> {
    const { data } = await apiClient.get<AppNotification[]>("/notifications");
    return data;
  },

  async unreadCount(): Promise<number> {
    const { data } = await apiClient.get<{ unread: number }>(
      "/notifications/unread-count",
    );
    return data.unread;
  },

  async markRead(id: string): Promise<AppNotification> {
    const { data } = await apiClient.post<AppNotification>(
      `/notifications/${id}/read`,
    );
    return data;
  },

  async markAllRead(): Promise<void> {
    await apiClient.post("/notifications/read-all");
  },
};

export const systemApi = {
  async features(): Promise<FeatureFlags> {
    const { data } = await apiClient.get<FeatureFlags>("/features");
    return data;
  },
};

export const gdprApi = {
  /** Tüm kullanıcı verisini JSON dosyası olarak indirir. */
  async exportData(): Promise<void> {
    const { data } = await apiClient.get<Blob>("/gdpr/export", {
      responseType: "blob",
    });
    const url = URL.createObjectURL(data);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "docassistant-export.json";
    anchor.click();
    URL.revokeObjectURL(url);
  },

  async deleteAccount(password: string): Promise<void> {
    await apiClient.post("/gdpr/delete-account", { password, confirm: true });
  },
};
