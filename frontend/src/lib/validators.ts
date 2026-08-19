import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Geçerli bir email girin."),
  password: z.string().min(1, "Parola gerekli."),
  totp_code: z.string().optional(),
});

export const registerSchema = z.object({
  email: z.string().email("Geçerli bir email girin."),
  password: z.string().min(8, "Parola en az 8 karakter olmalı."),
  full_name: z.string().max(255).optional(),
  organization_name: z.string().max(255).optional(),
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
