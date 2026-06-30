import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

import CheckoutView from "@/views/CheckoutView.vue";
import DashboardView from "@/views/DashboardView.vue";
import LoginView from "@/views/LoginView.vue";
import SettlementsView from "@/views/SettlementsView.vue";
import TransactionsView from "@/views/TransactionsView.vue";
import WebhookView from "@/views/WebhookView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/login",
      name: "login",
      component: LoginView,
      meta: { public: true },
    },
    {
      path: "/checkout/:id",
      name: "checkout",
      component: CheckoutView,
      meta: { public: true },
    },
    {
      path: "/",
      name: "dashboard",
      component: DashboardView,
    },
    {
      path: "/transactions",
      name: "transactions",
      component: TransactionsView,
    },
    {
      path: "/settlements",
      name: "settlements",
      component: SettlementsView,
    },
    {
      path: "/webhook",
      name: "webhook",
      component: WebhookView,
    },
  ],
});

router.beforeEach((to) => {
  const auth = useAuthStore();
  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: "login" };
  }
  if (to.meta.public && auth.isAuthenticated) {
    return { name: "dashboard" };
  }
});

export default router;
