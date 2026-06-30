<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import api from "@/services/api";

const route = useRoute();
const checkout = ref(null);
const isLoading = ref(true);
const error = ref("");
const paid = ref(false);
const paymentStatus = ref("");

onMounted(async () => {
  try {
    const response = await api.get(`/api/v1/checkout/${route.params.id}/`);
    checkout.value = response.data.data;
  } catch (err) {
    error.value = err.response?.data?.message || "Checkout não encontrado.";
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

async function copyPixCode() {
  if (!checkout.value?.first_pix?.pix_code) return;
  try {
    await navigator.clipboard.writeText(checkout.value.first_pix.pix_code);
    alert("Código Pix copiado!");
  } catch {
    alert("Não foi possível copiar automaticamente.");
  }
}

async function simulatePayment() {
  if (!checkout.value?.first_pix?.txid) return;
  paymentStatus.value = "processing";
  try {
    const response = await api.post("/api/v1/payments/simulate/", {
      txid: checkout.value.first_pix.txid,
    });
    if (response.data.data.status === "paid") {
      paid.value = true;
    } else {
      paymentStatus.value = response.data.data.status;
    }
  } catch (err) {
    paymentStatus.value = "error";
    error.value = err.response?.data?.message || "Erro ao simular pagamento.";
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 py-12 px-4">
    <div class="max-w-xl mx-auto">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-slate-900">Pagaê</h1>
        <p class="text-slate-500 mt-2">Checkout Pix parcelado</p>
      </div>

      <p v-if="isLoading" class="text-center text-slate-500">Carregando...</p>
      <p v-else-if="error" class="text-center text-red-600">{{ error }}</p>

      <div v-else-if="paid" class="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 text-center">
        <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span class="text-2xl">✓</span>
        </div>
        <h2 class="text-2xl font-bold text-slate-900 mb-2">Pagamento confirmado!</h2>
        <p class="text-slate-600">
          Sua primeira parcela foi paga. As próximas parcelas serão enviadas conforme o vencimento.
        </p>
      </div>

      <div v-else class="space-y-6">
        <div class="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <p class="text-sm text-slate-500">Lojista</p>
          <p class="text-lg font-semibold text-slate-900">{{ checkout.merchant_name }}</p>
        </div>

        <div class="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <h2 class="text-lg font-semibold text-slate-900 mb-4">Resumo do pedido</h2>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-slate-500">Cliente</span>
              <span class="font-medium text-slate-900">{{ checkout.customer_name }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-500">Valor total</span>
              <span class="font-medium text-slate-900">{{ formatCents(checkout.total_amount) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-500">Parcelas</span>
              <span class="font-medium text-slate-900">{{ checkout.installment_count }}x de {{ formatCents(checkout.installment_amount) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-500">Vencimento 1ª parcela</span>
              <span class="font-medium text-slate-900">{{ formatDate(checkout.schedule[0]?.due_date) }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <h2 class="text-lg font-semibold text-slate-900 mb-4">Pague a primeira parcela via Pix</h2>
          <div class="space-y-4">
            <div class="bg-slate-100 p-4 rounded-lg break-all text-sm font-mono text-slate-800">
              {{ checkout.first_pix?.pix_code || "Código Pix indisponível" }}
            </div>
            <button
              class="w-full py-2.5 bg-brand-600 hover:bg-brand-700 text-white font-semibold rounded-lg transition"
              @click="copyPixCode"
            >
              Copiar código Pix
            </button>
            <button
              class="w-full py-2.5 border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold rounded-lg transition"
              @click="simulatePayment"
            >
              Simular pagamento (sandbox)
            </button>
            <p v-if="paymentStatus === 'processing'" class="text-center text-slate-500 text-sm">Processando...</p>
            <p v-else-if="paymentStatus === 'error'" class="text-center text-red-600 text-sm">{{ error }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
