import { apiClient } from "@/lib/api-client";
import type { BillingUsage, Plan, PlanSpec, Subscription } from "@/types/api";

export const billingApi = {
  async plans(): Promise<PlanSpec[]> {
    const { data } = await apiClient.get<PlanSpec[]>("/billing/plans");
    return data;
  },

  async subscription(orgId: string): Promise<Subscription> {
    const { data } = await apiClient.get<Subscription>(
      `/billing/${orgId}/subscription`,
    );
    return data;
  },

  async usage(orgId: string): Promise<BillingUsage> {
    const { data } = await apiClient.get<BillingUsage>(`/billing/${orgId}/usage`);
    return data;
  },

  async checkout(orgId: string, plan: Plan): Promise<{ url: string }> {
    const { data } = await apiClient.post<{ session_id: string; url: string }>(
      `/billing/${orgId}/checkout`,
      { plan },
    );
    return data;
  },

  async portal(orgId: string): Promise<{ url: string }> {
    const { data } = await apiClient.post<{ url: string }>(
      `/billing/${orgId}/portal`,
    );
    return data;
  },
};

/** Kullanım oranını 0-100 aralığına sıkıştırır. */
export function usagePercent(used: number, limit: number): number {
  if (limit <= 0) return 100;
  return Math.min(100, Math.round((used / limit) * 100));
}

export function formatPrice(spec: PlanSpec): string {
  if (spec.price_monthly === 0) return "Ücretsiz";
  return `${spec.price_monthly} ${spec.currency} / ay`;
}
