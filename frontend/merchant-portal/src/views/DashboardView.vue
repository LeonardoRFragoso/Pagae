<script setup>
import { onMounted, ref } from "vue";

import AppLayout from "@/components/AppLayout.vue";
import api from "@/services/api";

const dashboard = ref(null);
const isLoading = ref(true);
const error = ref("");

onMounted(async () => {
  try {
    const response = await api.get("/api/v1/merchants/dashboard/");
    dashboard.value = response.data.data;
  } catch (err) {
    error.value = err.response?.data?.message || "Erro ao carregar dashboard.";
  } finally {
    isLoading.value = false;
  }
});

function formatCents(cents) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(cents / 100);
}
</script>

<template>
  <AppLayout>
    <div>
      <h2 class="text-2xl font-bold text-slate-900 mb-6">Dashboard</h2>

      <p v-if="isLoading" class="text-slate-500">Carregando...</p>
      <p v-else-if="error" class="text-red-600">{{ error }}</p>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div class="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
          <p class="text-sm text-slate-500 font-medium">GMV hoje</p>
          <p class="text-3xl font-bold text-slate-900 mt-2">
            {{ formatCents(dashboard.gmv_today) }}
          </p>
        </div>

        <div class="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
          <p class="text-sm text-slate-500 font-medium">GMV 7 dias</p>
          <p class="text-3xl font-bold text-slate-900 mt-2">
            {{ formatCents(dashboard.gmv_week) }}
          </p>
        </div>

        <div class="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
          <p class="text-sm text-slate-500 font-medium">GMV 30 dias</p>
          <p class="text-3xl font-bold text-slate-900 mt-2">
            {{ formatCents(dashboard.gmv_month) }}
          </p>
        </div>

        <div class="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
          <p class="text-sm text-slate-500 font-medium">Taxa de aprovação</p>
          <p class="text-3xl font-bold text-brand-600 mt-2">
            {{ dashboard.approval_rate }}%
          </p>
        </div>

        <div class="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
          <p class="text-sm text-slate-500 font-medium">Total de transações</p>
          <p class="text-3xl font-bold text-slate-900 mt-2">
            {{ dashboard.total_transactions }}
          </p>
        </div>

        <div class="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
          <p class="text-sm text-slate-500 font-medium">A receber</p>
          <p class="text-3xl font-bold text-slate-900 mt-2">
            {{ formatCents(dashboard.pending_settlement) }}
          </p>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
