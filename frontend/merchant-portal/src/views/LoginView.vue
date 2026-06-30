<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "@/stores/auth";

const email = ref("");
const password = ref("");
const auth = useAuthStore();
const router = useRouter();

async function handleLogin() {
  const ok = await auth.login(email.value, password.value);
  if (ok) {
    router.push({ name: "dashboard" });
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-900">
    <div class="w-full max-w-md bg-white rounded-2xl p-8 shadow-xl">
      <div class="mb-8 text-center">
        <h1 class="text-3xl font-bold text-slate-900">Pagaê</h1>
        <p class="text-slate-500 mt-2">Portal do lojista</p>
      </div>

      <form class="space-y-5" @submit.prevent="handleLogin">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Email</label>
          <input
            v-model="email"
            type="email"
            required
            class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Senha</label>
          <input
            v-model="password"
            type="password"
            required
            class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        <p v-if="auth.error" class="text-red-600 text-sm">{{ auth.error }}</p>

        <button
          type="submit"
          :disabled="auth.isLoading"
          class="w-full py-2.5 bg-brand-600 hover:bg-brand-700 text-white font-semibold rounded-lg transition disabled:opacity-50"
        >
          {{ auth.isLoading ? "Entrando..." : "Entrar" }}
        </button>
      </form>
    </div>
  </div>
</template>
