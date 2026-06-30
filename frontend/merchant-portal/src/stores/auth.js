import { defineStore } from "pinia";
import { computed, ref } from "vue";

import api from "@/services/api";

export const useAuthStore = defineStore("auth", () => {
  const accessToken = ref(localStorage.getItem("accessToken") || "");
  const refreshToken = ref(localStorage.getItem("refreshToken") || "");
  const user = ref(null);
  const merchant = ref(null);
  const isLoading = ref(false);
  const error = ref("");

  const isAuthenticated = computed(() => !!accessToken.value);

  function setTokens(tokens) {
    accessToken.value = tokens.access;
    refreshToken.value = tokens.refresh;
    localStorage.setItem("accessToken", tokens.access);
    localStorage.setItem("refreshToken", tokens.refresh);
    api.defaults.headers.common.Authorization = `Bearer ${tokens.access}`;
  }

  function clearTokens() {
    accessToken.value = "";
    refreshToken.value = "";
    user.value = null;
    merchant.value = null;
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    delete api.defaults.headers.common.Authorization;
  }

  async function login(email, password) {
    isLoading.value = true;
    error.value = "";
    try {
      const response = await api.post("/api/v1/auth/login/", { email, password });
      setTokens({ access: response.data.access, refresh: response.data.refresh });
      await fetchProfile();
      return true;
    } catch (err) {
      error.value = err.response?.data?.message || "Credenciais inválidas.";
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchProfile() {
    try {
      const me = await api.get("/api/v1/merchants/me/");
      merchant.value = me.data.data;
      user.value = { email: merchant.value.email };
    } catch (err) {
      clearTokens();
      throw err;
    }
  }

  async function logout() {
    try {
      await api.post("/api/v1/auth/logout/", { refresh: refreshToken.value });
    } finally {
      clearTokens();
    }
  }

  function initialize() {
    if (accessToken.value) {
      api.defaults.headers.common.Authorization = `Bearer ${accessToken.value}`;
    }
  }

  return {
    accessToken,
    refreshToken,
    user,
    merchant,
    isLoading,
    error,
    isAuthenticated,
    login,
    logout,
    fetchProfile,
    initialize,
  };
});
