import { describe, it, expect, beforeEach, vi } from "vitest";
import axios from "axios";
import apiClient, { tokenStore } from "../client";

// Fake backend: protected endpoint only accepts the token "good-access".
function installFakeBackend() {
  const calls = [];
  apiClient.defaults.adapter = async (config) => {
    calls.push(config.url);
    const auth = config.headers.Authorization;
    if (auth === "Bearer good-access") {
      return { data: { ok: true }, status: 200, statusText: "OK", headers: {}, config };
    }
    const err = new Error("Unauthorized");
    err.config = config;
    err.response = { status: 401, data: { detail: "Could not validate credentials" }, config };
    err.isAxiosError = true;
    throw err;
  };
  return calls;
}

beforeEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

describe("silent token refresh", () => {
  it("refreshes on 401 and retries the original request", async () => {
    tokenStore.set("expired-access", "refresh-1");
    const calls = installFakeBackend();
    const post = vi.spyOn(axios, "post").mockResolvedValue({
      data: { access_token: "good-access", refresh_token: "refresh-2" },
    });

    const res = await apiClient.get("/cart/cart");

    expect(res.data.ok).toBe(true);
    expect(post).toHaveBeenCalledTimes(1);
    expect(calls).toEqual(["/cart/cart", "/cart/cart"]); // failed once, retried once
    expect(tokenStore.getAccess()).toBe("good-access");
    expect(tokenStore.getRefresh()).toBe("refresh-2"); // rotated token is saved
  });

  it("runs only ONE refresh when several requests fail at once", async () => {
    tokenStore.set("expired-access", "refresh-1");
    installFakeBackend();
    const post = vi.spyOn(axios, "post").mockImplementation(
      () => new Promise((r) => setTimeout(() => r({ data: { access_token: "good-access", refresh_token: "refresh-2" } }), 20))
    );

    const results = await Promise.all([
      apiClient.get("/a"), apiClient.get("/b"), apiClient.get("/c"),
    ]);

    expect(results.every((r) => r.data.ok)).toBe(true);
    expect(post).toHaveBeenCalledTimes(1); // otherwise rotation would flag token theft
  });

  it("logs the user out when the refresh token is rejected", async () => {
    tokenStore.set("expired-access", "dead-refresh");
    installFakeBackend();
    vi.spyOn(axios, "post").mockRejectedValue({ response: { status: 401 } });

    await expect(apiClient.get("/cart/cart")).rejects.toBeTruthy();

    expect(tokenStore.getAccess()).toBeNull();
    expect(tokenStore.getRefresh()).toBeNull();
  });

  it("does not try to refresh for guests (no refresh token)", async () => {
    installFakeBackend();
    const post = vi.spyOn(axios, "post");

    await expect(apiClient.get("/cart/cart")).rejects.toBeTruthy();
    expect(post).not.toHaveBeenCalled();
  });

  it("does not refresh or log out on a wrong-password login 401", async () => {
    tokenStore.set("some-access", "refresh-1");
    installFakeBackend();
    const post = vi.spyOn(axios, "post");

    await expect(apiClient.post("/users/auth/login", {})).rejects.toBeTruthy();
    expect(post).not.toHaveBeenCalled();
    expect(tokenStore.getRefresh()).toBe("refresh-1");
  });

  it("uses a token another tab already refreshed instead of refreshing again", async () => {
    tokenStore.set("expired-access", "refresh-1");
    installFakeBackend();
    const post = vi.spyOn(axios, "post");
    // Simulate: request goes out with the old token, meanwhile another tab stores a new one.
    apiClient.interceptors.request.use((config) => {
      if (!config._sim) {
        config._sim = true;
        queueMicrotask(() => localStorage.setItem("token", "good-access"));
      }
      return config;
    });

    const res = await apiClient.get("/x");
    expect(res.data.ok).toBe(true);
    expect(post).not.toHaveBeenCalled();
  });
});
