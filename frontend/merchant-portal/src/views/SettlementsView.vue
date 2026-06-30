<script setup>
import { onMounted, ref } from "vue";

import AppLayout from "@/components/AppLayout.vue";
import api from "@/services/api";

const settlements = ref([]);
const isLoading = ref(true);
const error = ref("");

onMounted(async () => {
  try {
    const response = await api.get("/api/v1/merchants/settlements/");
    settlements.value = response.data.data;
  } catch (err) {
    error.value = err.response?.data?.message || "Erro ao carregar repasses.";
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

function formatDate(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("pt-BR").format(new Date(value));
}

function statusLabel(status) {
  const labels = {
    pending: "Pendente",
    paid: "Pago",
    failed: "Falhou",
  };
  return labels[status] || status;
}
</script>

<template>
  <AppLayout>
    <div>
      <h2 class="text-2xl font-bold text-slate-900 mb-6">Repasses</h2>

      <p v-if="isLoading" class="text-slate-500">Carregando...</p>
      <p v-else-if="error" class="text-red-600">{{ error }}</p>
      <p v-else-if="settlements.length === 0" class="text-slate-500">
        Nenhum repasse encontrado.
      </p>

      <div v-else class="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table class="w-full text-left">
          <thead class="bg-slate-50 text-slate-500 text-sm">
            <tr>
              <th class="px-6 py-3 font-medium">Período</th>
              <th class="px-6 py-3 font-medium">Valor</th>
              <th class="px-6 py-3 font-medium">Status</th>
              <th class="px-6 py-3 font-medium">Pago em</th>
              <th class="px-6 py-3 font-medium">E2E ID</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="settlement in settlements" :key="settlement.id" class="hover:bg-slate-50">
              <td class="px-6 py-4 text-sm">
                {{ formatDate(settlement.period_start) }} — {{ formatDate(settlement.period_end) }}
              </td>
              <td class="px-6 py-4 text-sm font-medium">{{ formatCents(settlement.amount) }}</td>
              <td class="px-6 py-4">
                <span
                  class="px-2 py-1 rounded-full text-xs font-semibold"
                  :class="{
                    'bg-green-100 text-green-700': settlement.status === 'paid',
                    'bg-yellow-100 text-yellow-700': settlement.status === 'pending',
                    'bg-red-100 text-red-700': settlement.status === 'failed',
                  }"
                >
                  {{ statusLabel(settlement.status) }}
                </span>
              </td>
              <td class="px-6 py-4 text-sm text-slate-500">{{ formatDate(settlement.paid_at) }}</td>
              <td class="px-6 py-4 text-sm text-slate-500 font-mono">{{ settlement.pix_e2e_id || "—" }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </AppLayout>
</template>
