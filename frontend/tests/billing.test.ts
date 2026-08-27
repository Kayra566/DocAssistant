import { describe, expect, it } from "vitest";

import { formatPrice, usagePercent } from "@/features/billing/api";
import type { PlanSpec } from "@/types/api";

function makePlan(overrides: Partial<PlanSpec>): PlanSpec {
  return {
    key: "pro",
    name: "Pro",
    price_monthly: 19,
    currency: "USD",
    documents: 100,
    storage_mb: 1024,
    ai_requests: 1000,
    ai_tokens: 2_000_000,
    features: [],
    ...overrides,
  };
}

describe("usagePercent", () => {
  it("computes a rounded percentage", () => {
    expect(usagePercent(25, 100)).toBe(25);
    expect(usagePercent(1, 3)).toBe(33);
  });

  it("caps at 100", () => {
    expect(usagePercent(500, 100)).toBe(100);
  });

  it("treats a zero limit as full", () => {
    expect(usagePercent(0, 0)).toBe(100);
  });
});

describe("formatPrice", () => {
  it("labels the free plan", () => {
    expect(formatPrice(makePlan({ key: "free", price_monthly: 0 }))).toBe(
      "Ücretsiz",
    );
  });

  it("formats paid plans with currency", () => {
    expect(formatPrice(makePlan({}))).toBe("19 USD / ay");
  });
});
