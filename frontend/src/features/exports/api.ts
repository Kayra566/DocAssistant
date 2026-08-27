import { apiClient } from "@/lib/api-client";
import type { ExportFormat, ExportJob } from "@/types/api";

export const EXPORT_FORMATS: { key: ExportFormat; label: string }[] = [
  { key: "pdf", label: "PDF" },
  { key: "docx", label: "DOCX" },
  { key: "xlsx", label: "XLSX" },
  { key: "md", label: "Markdown" },
];

export const exportApi = {
  async create(
    orgId: string,
    aiJobId: string,
    format: ExportFormat,
  ): Promise<ExportJob> {
    const { data } = await apiClient.post<ExportJob>(`/exports/${orgId}`, {
      ai_job_id: aiJobId,
      format,
    });
    return data;
  },

  async list(orgId: string, aiJobId?: string): Promise<ExportJob[]> {
    const { data } = await apiClient.get<ExportJob[]>(`/exports/${orgId}`, {
      params: aiJobId ? { ai_job_id: aiJobId } : undefined,
    });
    return data;
  },

  /** Dosyayı auth başlığıyla indirir ve tarayıcıda kaydetme akışını tetikler. */
  async download(orgId: string, exportJob: ExportJob): Promise<void> {
    const { data } = await apiClient.get<Blob>(
      `/exports/${orgId}/${exportJob.id}/download`,
      { responseType: "blob" },
    );
    const url = URL.createObjectURL(data);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = exportJob.filename;
    anchor.click();
    URL.revokeObjectURL(url);
  },
};
