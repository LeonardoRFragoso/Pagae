import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAuthStore } from "@/stores/auth";
import api from "@/services/api";

vi.mock("@/services/api", () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    defaults: { headers: { common: {} } },
  },
}));

describe("AuthStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("logs in and stores tokens", async () => {
    api.post.mockResolvedValueOnce({ data: { access: "acc", refresh: "ref" } });
    api.get.mockResolvedValueOnce({ data: { data: { email: "loja@teste.com", trade_name: "Loja Teste" } } });

    const auth = useAuthStore();
    const ok = await auth.login("loja@teste.com", "secret");

    expect(ok).toBe(true);
    expect(auth.accessToken).toBe("acc");
    expect(api.defaults.headers.common.Authorization).toBe("Bearer acc");
    expect(api.post).toHaveBeenCalledWith("/api/v1/auth/login/", { email: "loja@teste.com", password: "secret" });
  });

  it("returns false on failed login", async () => {
    api.post.mockRejectedValueOnce({ response: { data: { message: "Invalid" } } });

    const auth = useAuthStore();
    const ok = await auth.login("bad", "bad");

    expect(ok).toBe(false);
    expect(auth.error).toBe("Invalid");
  });

  it("clears tokens on logout", async () => {
    api.post.mockResolvedValueOnce({});
    api.defaults.headers.common.Authorization = "Bearer x";

    const auth = useAuthStore();
    auth.accessToken = "x";
    auth.refreshToken = "y";
    await auth.logout();

    expect(auth.accessToken).toBe("");
    expect(api.defaults.headers.common.Authorization).toBeUndefined();
    expect(api.post).toHaveBeenCalledWith("/api/v1/auth/logout/", { refresh: "y" });
  });
});
