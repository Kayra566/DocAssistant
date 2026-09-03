import { z } from "zod";

/**
 * Doldurulmamış metin girdileri "" üretir; backend bunu boş string olarak
 * doğrular ve 422 döner. Opsiyonel alanları undefined'a çevirip gönderimden düşürüyoruz.
 */
const optionalText = (max = 255) =>
  z
    .string()
    .max(max)
    .trim()
    .optional()
    .transform((value) => (value ? value : undefined));

export const loginSchema = z.object({
  email: z.string().email("Geçerli bir email girin."),
  password: z.string().min(1, "Parola gerekli."),
  totp_code: optionalText(10),
});

export const registerSchema = z.object({
  email: z.string().email("Geçerli bir email girin."),
  password: z.string().min(8, "Parola en az 8 karakter olmalı."),
  full_name: optionalText(),
  organization_name: optionalText(),
});

export const forgotSchema = z.object({
  email: z.string().email("Geçerli bir email girin."),
});

export const resetSchema = z.object({
  token: z.string().min(1, "Token gerekli."),
  new_password: z.string().min(8, "Parola en az 8 karakter olmalı."),
});

export type LoginInput = z.infer<typeof loginSchema>;
export type RegisterInput = z.infer<typeof registerSchema>;
export type ForgotInput = z.infer<typeof forgotSchema>;
export type ResetInput = z.infer<typeof resetSchema>;
