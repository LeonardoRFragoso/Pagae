<script setup>
import { useRouter } from "vue-router";

import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();

async function logout() {
  await auth.logout();
  router.push({ name: "login" });
}

const nav = [
  { name: "Dashboard", to: "/", icon: "📊" },
  { name: "Transações", to: "/transactions", icon: "🛒" },
  { name: "Repasses", to: "/settlements", icon: "💰" },
  { name: "Webhook", to: "/webhook", icon: "🔗" },
];
</script>

<template>
  <div class="flex min-h-screen">
    <aside class="w-64 bg-slate-900 text-white p-6 flex flex-col">
      <div class="mb-10">
        <h1 class="text-2xl font-bold tracking-tight">Pagaê</h1>
        <p class="text-slate-400 text-sm">Portal do lojista</p>
      </div>

      <nav class="space-y-2 flex-1">
        <RouterLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 px-4 py-3 rounded-lg transition hover:bg-slate-800"
          active-class="bg-brand-600"
        >
          <span>{{ item.icon }}</span>
          <span>{{ item.name }}</span>
        </RouterLink>
      </nav>

      <div class="border-t border-slate-700 pt-4 mt-4">
        <p class="text-sm text-slate-300 truncate">
          {{ auth.merchant?.trade_name || auth.user?.email }}
        </p>
        <button
          class="mt-3 text-sm text-slate-400 hover:text-white transition"
          @click="logout"
        >
          Sair
        </button>
      </div>
    </aside>

    <main class="flex-1 p-8">
      <slot />
    </main>
  </div>
</template>
