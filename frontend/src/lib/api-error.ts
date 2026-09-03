import { AxiosError } from "axios";

/** FastAPI doğrulama hatası kaydı (422 yanıtlarında dizi olarak döner). */
interface ValidationDetail {
  loc?: (string | number)[];
  msg?: string;
}

function isValidationDetail(value: unknown): value is ValidationDetail {
  return typeof value === "object" && value !== null && "msg" in value;
}

/**
 * API hatasını her zaman render edilebilir bir metne çevirir.
 *
 * FastAPI iki farklı `detail` biçimi döndürür: uygulama hatalarında string,
 * 422 doğrulama hatalarında nesne dizisi. Dizi doğrudan JSX'e verilirse React
 * "Objects are not valid as a React child" hatasıyla tüm ağacı düşürür.
 */
export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (!(error instanceof AxiosError)) {
    return error instanceof Error && error.message ? error.message : fallback;
  }

  if (error.response?.status === 429) {
    return "Çok fazla deneme yaptınız. Lütfen bir dakika bekleyip tekrar deneyin.";
  }

  const detail: unknown = error.response?.data?.detail;

  if (typeof detail === "string" && detail.trim()) return detail;

  if (Array.isArray(detail)) {
    const messages = detail
      .filter(isValidationDetail)
      .map((item) => {
        const field = item.loc?.filter((part) => part !== "body").join(".");
        return field ? `${field}: ${item.msg}` : item.msg;
      })
      .filter(Boolean);
    if (messages.length > 0) return messages.join(" · ");
  }

  if (isValidationDetail(detail) && detail.msg) return detail.msg;

  if (!error.response) {
    return "Sunucuya ulaşılamadı. Bağlantınızı kontrol edin.";
  }

  return fallback;
}
