import { AxiosError, AxiosHeaders } from "axios";
import { describe, expect, it } from "vitest";

import { getApiErrorMessage } from "@/lib/api-error";

function axiosError(status: number, data: unknown): AxiosError {
  const error = new AxiosError("Request failed");
  error.response = {
    status,
    statusText: "",
    data,
    headers: new AxiosHeaders(),
    config: { headers: new AxiosHeaders() },
  };
  return error;
}

describe("getApiErrorMessage", () => {
  it("uygulama hatasındaki string detail'i döndürür", () => {
    const error = axiosError(409, { detail: "Bu email ile zaten bir hesap var." });
    expect(getApiErrorMessage(error, "fallback")).toBe(
      "Bu email ile zaten bir hesap var.",
    );
  });

  it("422 doğrulama dizisini okunur metne çevirir", () => {
    const error = axiosError(422, {
      detail: [
        { type: "string_too_short", loc: ["body", "password"], msg: "too short" },
        { type: "value_error", loc: ["body", "email"], msg: "invalid email" },
      ],
    });

    const message = getApiErrorMessage(error, "fallback");

    expect(message).toBe("password: too short · email: invalid email");
    expect(typeof message).toBe("string");
  });

  it("rate limit için açıklayıcı mesaj verir", () => {
    const error = axiosError(429, { detail: "Çok fazla istek gönderildi." });
    expect(getApiErrorMessage(error, "fallback")).toContain("bir dakika");
  });

  it("yanıt yoksa ağ hatası bildirir", () => {
    expect(getApiErrorMessage(new AxiosError("Network Error"), "fallback")).toBe(
      "Sunucuya ulaşılamadı. Bağlantınızı kontrol edin.",
    );
  });

  it("tanınmayan gövdede fallback kullanır", () => {
    expect(getApiErrorMessage(axiosError(500, {}), "Bir hata oluştu.")).toBe(
      "Bir hata oluştu.",
    );
  });
});
