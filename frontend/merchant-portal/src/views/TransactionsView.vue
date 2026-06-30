<script setup>
import { computed, onMounted, ref } from "vue";

import AppLayout from "@/components/AppLayout.vue";
import api from "@/services/api";

const transactions = ref([]);
const selected = ref(null);
const isLoading = ref(true);
const error = ref("");
const statusFilter = ref("");

const statusOptions = [
  { value: "", label: "Todos" },
  { value: "approved", label: "Aprovado" },
  { value: "pending", label: "Pendente" },
  { value: "denied", label: "Negado" },
];

onMounted(async () => {
  try {
    const response = await api.get("/api/v1/merchants/transactions/");
    transactions.value = response.data.data;
  } catch (err) {
    error.value = err.response?.data?.message || "Erro ao carregar transações.";
  } finally {
    isLoading.value = false;
  }
});

const filteredTransactions = computed(() => {
  if (!statusFilter.value) return transactions.value;
  return transactions.value.filter((t) => t.status === statusFilter.value);
});

async function openDetail(transaction) {
  try {
    const response = await api.get(`/api/v1/merchants/transactions/${transaction.id}/`);
    selected.value = response.data.data;
  } catch (err) {
    error.value = err.response?.data?.message || "Erro ao carregar detalhes.";
  }
}

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
    approved: "Aprovado",
    pending: "Pendente",
    denied: "Negado",
    completed: "Concluído",
    expired: "Expirado",
    cancelled: "Cancelado",
  };
  return labels[status] || status;
}
</script>

<template>
  <AppLayout>
    <div>
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-2xl font-bold text-slate-900">Transações</h2>
        <select
          v-model="statusFilter"
          class="px-3 py-2 border border-slate-300 rounded-lg text-sm"
        >
          <option v-for="option in statusOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>

      <p v-if="isLoading" class="text-slate-500">Carregando...</p>
      <p v-else-if="error" class="text-red-600">{{ error }}</p>
      <p v-else-if="filteredTransactions.length === 0" class="text-slate-500">
        Nenhuma transação encontrada.
      </p>

      <div v-else class="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table class="w-full text-left">
          <thead class="bg-slate-50 text-slate-500 text-sm">
            <tr>
              <th class="px-6 py-3 font-medium">Pedido</th>
              <th class="px-6 py-3 font-medium">Cliente</th>
              <th class="px-6 py-3 font-medium">Valor</th>
              <th class="px-6 py-3 font-medium">Parcelas</th>
              <th class="px-6 py-3 font-medium">Status</th>
              <th class="px-6 py-3 font-medium">Data</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr
              v-for="transaction in filteredTransactions"
              :key="transaction.id"
              class="hover:bg-slate-50 cursor-pointer"
              @click="openDetail(transaction)"
            >
              <td class="px-6 py-4 text-sm">{{ transaction.merchant_order_id || transaction.id }}</td>
              <td class="px-6 py-4 text-sm">{{ transaction.customer_name }}</td>
              <td class="px-6 py-4 text-sm font-medium">{{ formatCents(transaction.total_amount) }}</td>
              <td class="px-6 py-4 text-sm">{{ transaction.installment_count }}x</td>
              <td class="px-6 py-4">
                <span
                  class="px-2 py-1 rounded-full text-xs font-semibold"
                  :class="{
                    'bg-green-100 text-green-700': transaction.status === 'approved',
                    'bg-yellow-100 text-yellow-700': transaction.status === 'pending',
                    'bg-red-100 text-red-700': transaction.status === 'denied',
                    'bg-slate-100 text-slate-600': !['approved', 'pending', 'denied'].includes(transaction.status),
                  }"
                >
                  {{ statusLabel(transaction.status) }}
                </span>
              </td>
              <td class="px-6 py-4 text-sm text-slate-500">{{ formatDate(transaction.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div
        v-if="selected"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="selected = null"
      >
        <div class="bg-white rounded-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-xl font-bold">Detalhes da transação</h3>
            <button class="text-slate-500 hover:text-slate-900" @click="selected = null">✕</button>
          </div>

          <div class="grid grid-cols-2 gap-4 mb-6">
            <div>
              <p class="text-sm text-slate-500">Pedido</p>
              <p class="font-medium">{{ selected.merchant_order_id || selected.id }}</p>
            </div>
            <div>
              <p class="text-sm text-slate-500">Cliente</p>
              <p class="font-medium">{{ selected.customer_name }}</p>
            </div>
            <div>
              <p class="text-sm text-slate-500">Total</p>
              <p class="font-medium">{{ formatCents(selected.total_amount) }}</p>
            </div>
            <div>
              <p class="text-sm text-slate-500">Líquido</p>
              <p class="font-medium">{{ formatCents(selected.net_amount) }}</p>
            </div>
          </div>

          <h4 class="font-semibold mb-3">Parcelas</h4>
          <table class="w-full text-left text-sm">
            <thead class="bg-slate-50 text-slate-500">
              <tr>
                <th class="px-4 py-2">#</th>
                <th class="px-4 py-2">Vencimento</th>
                <th class="px-4 py-2">Valor</th>
                <th class="px-4 py-2">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="installment in selected.installments" :key="installment.id">
                <td class="px-4 py-2">{{ installment.number }}</td>
                <td class="px-4 py-2">{{ formatDate(installment.due_date) }}</td>
                <td class="px-4 py-2">{{ formatCents(installment.amount) }}</td>
                <td class="px-4 py-2">
                  <span
                    class="px-2 py-0.5 rounded-full text-xs font-semibold"
                    :class="{
                      'bg-green-100 text-green-700': installment.status === 'paid',
                      'bg-yellow-100 text-yellow-700': installment.status === 'pending',
                      'bg-red-100 text-red-700': installment.status === 'overdue',
                    }"
                  >
                    {{ installment.status === 'paid' ? 'Pago' : installment.status === 'pending' ? 'Pendente' : 'Atrasado' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
