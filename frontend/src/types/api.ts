export type Role = "owner" | "admin" | "member" | "viewer";
export type Plan = "free" | "pro" | "business";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_verified: boolean;
  is_superuser: boolean;
  totp_enabled: boolean;
  created_at: string;
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: Plan;
  created_at: string;
}

export interface Member {
  user_id: string;
  email: string;
  full_name: string | null;
  role: Role;
}

export interface RegisterResponse {
  user: User;
  organization_id: string;
  dev_verification_token: string | null;
}

export interface MessageResponse {
  message: string;
  dev_token?: string | null;
}

export type DocumentStatus = "uploaded" | "processing" | "ready" | "failed";

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  mime_type: string;
  size_bytes: number;
  status: DocumentStatus;
  error: string | null;
  page_count: number;
  chunk_count: number;
  is_favorite: boolean;
  created_at: string;
}
