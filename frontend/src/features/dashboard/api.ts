import { apiClient } from "@/lib/api-client";
import type {
  ActivityEntry,
  DashboardStats,
  PlatformOrganization,
  PlatformStats,
} from "@/types/api";

export const dashboardApi = {
  async stats(orgId: string): Promise<DashboardStats> {
    const { data } = await apiClient.get<DashboardStats>(
      `/dashboard/${orgId}/stats`,
    );
    return data;
  },

  async activity(orgId: string, limit = 20): Promise<ActivityEntry[]> {
    const { data } = await apiClient.get<ActivityEntry[]>(
      `/dashboard/${orgId}/activity`,
      { params: { limit } },
    );
    return data;
  },
};

export const adminApi = {
  async stats(): Promise<PlatformStats> {
    const { data } = await apiClient.get<PlatformStats>("/admin/stats");
    return data;
  },

  async organizations(): Promise<PlatformOrganization[]> {
    const { data } = await apiClient.get<PlatformOrganization[]>(
      "/admin/organizations",
    );
    return data;
  },
};

const ACTION_LABELS: Record<string, string> = {
  "document.uploaded": "doküman yükledi",
  "document.deleted": "doküman sildi",
  "document.downloaded": "doküman indirdi",
  "share.created": "paylaşım bağlantısı oluşturdu",
  "share.revoked": "paylaşımı iptal etti",
  "share.accessed": "paylaşım bağlantısı açıldı",
  "comment.created": "yorum ekledi",
  "comment.deleted": "yorum sildi",
  "export.created": "sonucu dışa aktardı",
};

export function describeActivity(entry: ActivityEntry): string {
  const actor = entry.actor_email ?? "Bağlantı ziyaretçisi";
  const action = ACTION_LABELS[entry.action] ?? entry.action;
  const filename = entry.meta?.filename;
  return filename ? `${actor} ${action}: ${filename}` : `${actor} ${action}`;
}

const JOB_TYPE_LABELS: Record<string, string> = {
  chat: "Sohbet",
  summary: "Özet",
  keypoints: "Kritik Bilgi",
  quiz: "Quiz",
  translate: "Çeviri",
  extract: "Veri Çıkarma",
  compare: "Karşılaştırma",
};

export function jobTypeLabel(key: string): string {
  return JOB_TYPE_LABELS[key] ?? key;
}

/** Grafik ekseninde gün/ay biçiminde kısa etiket. */
export function shortDate(iso: string): string {
  const [, month, day] = iso.split("-");
  return `${day}.${month}`;
}
