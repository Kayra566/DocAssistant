import { beforeEach, describe, expect, it } from "vitest";

import { useAuthStore } from "@/stores/authStore";

describe("authStore", () => {
  beforeEach(() => {
    useAuthStore.getState().clear();
  });

  it("starts unauthenticated", () => {
    expect(useAuthStore.getState().isAuthenticated()).toBe(false);
  });

  it("stores tokens and marks authenticated", () => {
    useAuthStore.getState().setTokens("access-123", "refresh-456");
    const state = useAuthStore.getState();
    expect(state.accessToken).toBe("access-123");
    expect(state.refreshToken).toBe("refresh-456");
    expect(state.isAuthenticated()).toBe(true);
  });

  it("clears tokens on logout", () => {
    useAuthStore.getState().setTokens("a", "b");
    useAuthStore.getState().clear();
    expect(useAuthStore.getState().isAuthenticated()).toBe(false);
  });
});
