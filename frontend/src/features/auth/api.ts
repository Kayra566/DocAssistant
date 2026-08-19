import { apiClient } from "@/lib/api-client";
import type {
  MessageResponse,
  Organization,
  Member,
  RegisterResponse,
  Tokens,
  User,
} from "@/types/api";

export const authApi = {
  async register(payload: {
    email: string;
    password: string;
    full_name?: string;
    organization_name?: string;
  }): Promise<RegisterResponse> {
    const { data } = await apiClient.post<RegisterResponse>(
      "/auth/register",
      payload,
    );
    return data;
  },

  async login(payload: {
    email: string;
    password: string;
    totp_code?: string;
  }): Promise<Tokens> {
    const { data } = await apiClient.post<Tokens>("/auth/login", payload);
    return data;
  },

  async me(): Promise<User> {
    const { data } = await apiClient.get<User>("/auth/me");
    return data;
  },

  async verifyEmail(token: string): Promise<MessageResponse> {
    const { data } = await apiClient.post<MessageResponse>("/auth/verify-email", {
      token,
    });
    return data;
  },

  async forgotPassword(email: string): Promise<MessageResponse> {
    const { data } = await apiClient.post<MessageResponse>(
      "/auth/forgot-password",
      { email },
    );
    return data;
  },

  async resetPassword(token: string, newPassword: string): Promise<MessageResponse> {
    const { data } = await apiClient.post<MessageResponse>("/auth/reset-password", {
      token,
      new_password: newPassword,
    });
    return data;
  },

  async logout(refreshToken: string): Promise<void> {
    await apiClient.post("/auth/logout", { refresh_token: refreshToken });
  },
};

export const orgApi = {
  async list(): Promise<Organization[]> {
    const { data } = await apiClient.get<Organization[]>("/organizations");
    return data;
  },

  async members(orgId: string): Promise<Member[]> {
    const { data } = await apiClient.get<Member[]>(
      `/organizations/${orgId}/members`,
    );
    return data;
  },

  async invite(orgId: string, email: string, role: string) {
    const { data } = await apiClient.post(
      `/organizations/${orgId}/invitations`,
      { email, role },
    );
    return data;
  },
};
