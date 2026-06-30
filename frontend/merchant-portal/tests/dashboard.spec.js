import { mount, flushPromises, RouterLinkStub } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import DashboardView from "@/views/DashboardView.vue";
import api from "@/services/api";

vi.mock("@/services/api", () => ({
  default: {
    get: vi.fn(),
  },
}));

vi.mock("@/stores/auth", () => ({
  useAuthStore: vi.fn(() => ({ merchant: { trade_name: "Loja Teste" }, user: { email: "loja@teste.com" } })),
}));

describe("DashboardView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("renders dashboard cards", async () => {
    api.get.mockResolvedValueOnce({
      data: {
        data: {
          gmv_today: 10000,
          gmv_week: 50000,
          gmv_month: 200000,
          approval_rate: 95.5,
          total_transactions: 10,
          pending_settlement: 15000,
        },
      },
    });

    const wrapper = mount(DashboardView, {
      global: {
        stubs: { RouterLink: RouterLinkStub },
        provide: { router: { push: vi.fn(), beforeEach: vi.fn() } },
      },
    });
    await flushPromises();

    expect(wrapper.text()).toMatch(/R\$\s?100[.,]00/);
    expect(wrapper.text()).toContain("95.5%");
    expect(wrapper.text()).toContain("10");
  });

  it("shows error message when request fails", async () => {
    api.get.mockRejectedValueOnce({ response: { data: { message: "fail" } } });

    const wrapper = mount(DashboardView, {
      global: {
        stubs: { RouterLink: RouterLinkStub },
        provide: { router: { push: vi.fn(), beforeEach: vi.fn() } },
      },
    });
    await flushPromises();

    expect(wrapper.text()).toContain("fail");
  });
});
