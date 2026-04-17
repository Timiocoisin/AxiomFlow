<template>
  <div class="auth-shell min-h-screen flex flex-col">
    <nav class="sticky top-0 z-50 glass border-b dark:border-slate-800">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16 items-center">
          <button class="flex items-center gap-2" type="button" @click="goAuth">
            <img alt="Axiomflow Logo" class="w-8 h-8 rounded-lg" src="/icons/favicon.svg" />
            <span class="text-xl font-bold tracking-tight">Axiomflow</span>
          </button>
          <button
            class="h-10 w-10 inline-flex items-center justify-center rounded-full transition-colors text-slate-700 hover:bg-slate-900/5 dark:text-slate-200 dark:hover:bg-white/10"
            type="button"
            @click="$emit('toggle-theme')"
          >
            <Icon class="text-xl" icon="ph:moon-bold" :class="{ hidden: isDark }" />
            <Icon class="text-xl text-yellow-400" icon="ph:sun-bold" :class="{ hidden: !isDark }" />
          </button>
        </div>
      </div>
    </nav>

    <div class="flex-grow flex items-center justify-center p-4">
      <div class="w-full max-w-md bg-white dark:bg-slate-900 rounded-3xl p-8 lg:p-10 shadow-2xl border dark:border-slate-800">
        <h1 class="text-2xl font-bold mb-2">重置密码</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400 mb-8">请输入邮件中的 6 位验证码，并设置新密码。</p>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-500 dark:text-slate-400 mb-2">验证码</label>
            <input
              v-model.trim="token"
              class="w-full h-12 px-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 font-mono tracking-widest"
              placeholder="6 位字母或数字"
              type="text"
              autocomplete="one-time-code"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-500 dark:text-slate-400 mb-2">新密码</label>
            <input
              v-model="newPassword"
              class="w-full h-12 px-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
              placeholder="至少 8 位，含英文与数字"
              type="password"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-500 dark:text-slate-400 mb-2">确认新密码</label>
            <input
              v-model="confirmPassword"
              class="w-full h-12 px-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
              type="password"
            />
          </div>
          <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
          <button
            class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3.5 rounded-xl transition-all"
            :disabled="submitting"
            type="button"
            @click="submit"
          >
            {{ submitting ? "提交中…" : "完成重置" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { Icon } from "@iconify/vue";
import * as authApi from "./api/auth";

defineProps<{ isDark: boolean }>();
const emit = defineEmits<{ (e: "toggle-theme"): void; (e: "done"): void }>();

const token = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const error = ref("");
const submitting = ref(false);

function readTokenFromHash(): string {
  const hash = window.location.hash || "";
  const q = hash.indexOf("?");
  if (q < 0) return "";
  const params = new URLSearchParams(hash.slice(q + 1));
  return (params.get("token") || "").trim();
}

function goAuth() {
  window.location.hash = "#/auth";
  emit("done");
}

async function submit() {
  error.value = "";
  const t = token.value.trim();
  if (!/^[A-Za-z0-9]{6}$/.test(t)) {
    error.value = "请输入邮件中的 6 位验证码";
    return;
  }
  if (newPassword.value.length < 8 || !/[A-Za-z]/.test(newPassword.value) || !/\d/.test(newPassword.value)) {
    error.value = "新密码至少 8 位，且包含英文和数字";
    return;
  }
  if (newPassword.value !== confirmPassword.value) {
    error.value = "两次输入的密码不一致";
    return;
  }
  submitting.value = true;
  try {
    await authApi.resetPassword({ token: t, new_password: newPassword.value });
    window.location.hash = "#/auth";
    emit("done");
  } catch {
    error.value = "重置失败，验证码可能已过期";
  } finally {
    submitting.value = false;
  }
}

onMounted(() => {
  const t = readTokenFromHash();
  if (t) token.value = t;
});
</script>
