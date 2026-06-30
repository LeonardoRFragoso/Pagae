<script setup>
import { onMounted, ref } from "vue";

import AppLayout from "@/components/AppLayout.vue";
import api from "@/services/api";

const webhookUrl = ref("");
const webhookSecret = ref("");
const isLoading = ref(true);
const isSaving = ref(false);
const message = ref("");
const error = ref("");

onMounted(async () => {
  try {
    const response = await api.get("/api/v1/merchants/webhook/");
    webhookUrl.value = response.data.data.webhook_url || "";
    webhookSecret.value = response.data.data.webhook_secret || "";
  } catch (err) {
    error.value = err.response?.data?.message || "Erro ao carregar configuração.";
  } finally {
    isLoading.value = false;
  }
});

async function save() {
  isSaving.value = true;
  message.value = "";
  error.value = "";
  try {
    const response = await api.patch("/api/v1/merchants/webhook/", {
      webhook_url: webhookUrl.value,
      webhook_secret: webhookSecret.value,
    });
    webhookUrl.value = response.data.data.webhook_url;
    webhookSecret.value = response.data.data.webhook_secret;
    message.value = "Configuração salva com sucesso.";
  } catch (err) {
    error.value = err.response?.data?.message || "Erro ao salvar configuração.";
  } finally {
    isSaving.value = false;
  }
}

async function testWebhook() {
  message.value = "";
  error.value = "";
  try {
    await api.post("/api/v1/merchants/webhook/test/", { url: webhookUrl.value, secret: webhookSecret.value });
    message.value = "Webhook enviado com sucesso.";
  } catch (err) {
    error.value = err.response?.data?.message || "Erro ao testar webhook.";
  }
}
</script>

<template>
  <AppLayout>
    <div class="max-w-2xl">
      <h2 class="text-2xl font-bold text-slate-900 mb-6">Configuração de Webhook</h2>

      <p v-if="isLoading" class="text-slate-500">Carregando...</p>
      <p v-else-if="error" class="text-red-600">{{ error }}</p>

      <div v-else class="bg-white rounded-xl p-6 border border-slate-200 space-y-5">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">URL do Webhook</label>
          <input
            v-model="webhookUrl"
            type="url"
            class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
            placeholder="https://seusite.com/webhook/pagae"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Secret (HMAC)</label>
          <input
            v-model="webhookSecret"
            type="text"
            class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
            placeholder="whsec_..."
          />
          <p class="text-xs text-slate-500 mt-1">
            O Pagaê assinará cada evento com HMAC-SHA256 usando esse secret.
          </p>
        </div>

        <p v-if="message" class="text-green-600 text-sm">{{ message }}</p>
        <p v-if="error" class="text-red-600 text-sm">{{ error }}</p>

        <div class="flex gap-3">
          <button
            :disabled="isSaving"
            class="px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white font-semibold rounded-lg transition disabled:opacity-50"
            @click="save"
          >
            {{ isSaving ? "Salvando..." : "Salvar" }}
          </button>
          <button
            class="px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg transition"
            @click="testWebhook"
          >
            Testar
          </button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
