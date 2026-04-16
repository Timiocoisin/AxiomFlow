<template>
  <div class="auth-shell min-h-screen flex flex-col">
    <nav class="sticky top-0 z-50 glass border-b dark:border-slate-800">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16 items-center">
          <button class="flex items-center gap-2" type="button" @click="$emit('back')">
            <img alt="Axiomflow Logo" class="w-8 h-8 rounded-lg" src="/icons/favicon.svg" />
            <span class="text-xl font-bold tracking-tight">Axiomflow</span>
          </button>
          <div class="flex items-center gap-3">
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
      </div>
    </nav>

    <div class="flex-grow flex items-center justify-center p-4">
      <div v-if="!verified" class="bg-white dark:bg-slate-900 rounded-3xl p-10 text-center shadow-2xl border dark:border-slate-800 verify-card-glow w-full max-w-xl">
        <div class="mb-8 inline-flex items-center justify-center w-24 h-24 rounded-full bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 animate-pulse">
          <Icon class="text-5xl" icon="ph:envelope-open-bold" />
        </div>
        <h1 class="text-3xl font-bold mb-4">查收您的邮箱</h1>
        <p class="text-slate-500 dark:text-slate-400 mb-8 leading-relaxed">
          我们已向 <span class="text-slate-900 dark:text-white font-semibold">{{ maskedEmail }}</span> 发送验证邮件。请点击邮件里的链接完成激活。
        </p>
        <div class="space-y-4">
          <p v-if="statusText" class="text-sm text-slate-500 dark:text-slate-400">{{ statusText }}</p>
          <div class="pt-6 border-t dark:border-slate-800">
            <p class="text-sm text-slate-500 mb-4">没有收到邮件？</p>
            <button
              class="text-indigo-600 dark:text-indigo-400 font-semibold hover:underline decoration-2 underline-offset-4 disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="countingDown"
              type="button"
              @click="resend"
            >
              {{ countingDown ? `重新发送 (${countdown}s)` : "重新发送验证邮件" }}
            </button>
          </div>
        </div>
      </div>

      <div v-else class="bg-white dark:bg-slate-900 rounded-3xl p-10 text-center shadow-2xl border border-green-100 dark:border-green-900/30 w-full max-w-xl">
        <div class="mb-8 inline-flex items-center justify-center w-24 h-24 rounded-full bg-green-50 dark:bg-green-900/30 text-green-500">
          <Icon class="text-5xl" icon="ph:check-circle-bold" />
        </div>
        <h1 class="text-3xl font-bold mb-4">验证成功！</h1>
        <p class="text-slate-500 dark:text-slate-400 mb-8">您的邮箱已通过验证。现在您可以开始翻译您的第一个 PDF 文档了。</p>
        <button
          class="inline-block w-full bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-bold py-4 rounded-xl transition-all"
          type="button"
          @click="emit('verified', { accessToken })"
        >
          进入工作台
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { Icon } from "@iconify/vue";
import * as authApi from "./api/auth";

const props = defineProps<{ isDark: boolean; email?: string }>();

const emit = defineEmits<{
  (e: "toggle-theme"): void;
  (e: "back"): void;
  (e: "verified", payload: { accessToken: string }): void;
}>();

const verified = ref(false);
const countdown = ref(60);
const countingDown = ref(false);
let timer: number | null = null;
const statusText = ref("");
const accessToken = ref("");

const maskedEmail = computed(() => {
  const v = props.email || localStorage.getItem("axiomflow:lastRegisterEmail") || "您的邮箱";
  if (!v.includes("@")) return v;
  const [name, domain] = v.split("@");
  const safe = name.length <= 2 ? `${name[0] ?? "*"}*` : `${name.slice(0, 2)}***`;
  return `${safe}@${domain}`;
});

function getTokenFromHash(): string | null {
  const hash = window.location.hash || "";
  const qIndex = hash.indexOf("?");
  if (qIndex < 0) return null;
  const query = hash.slice(qIndex + 1);
  const params = new URLSearchParams(query);
  return params.get("token");
}

function openMailHint() {
  statusText.value = "请打开邮箱，点击验证链接即可自动完成验证。";
}

function startCountdown() {
  if (countingDown.value) return;
  countingDown.value = true;
  timer = window.setInterval(() => {
    countdown.value -= 1;
    if (countdown.value <= 0) {
      if (timer) window.clearInterval(timer);
      timer = null;
      countdown.value = 60;
      countingDown.value = false;
    }
  }, 1000);
}

function resend() {
  const email = props.email || localStorage.getItem("axiomflow:lastRegisterEmail") || "";
  if (!email) {
    statusText.value = "缺少邮箱信息，请返回注册页重新发送。";
    return;
  }
  authApi
    .resendVerification({ email })
    .then(() => {
      statusText.value = "已重新发送验证邮件，请查收。";
      startCountdown();
    })
    .catch(() => {
      statusText.value = "发送失败，请稍后重试。";
    });
}

async function tryVerifyFromToken() {
  const token = getTokenFromHash();
  if (!token) return;
  statusText.value = "正在验证，请稍候…";
  try {
    const res = await authApi.verifyEmail({ token });
    verified.value = true;
    accessToken.value = res.access_token;
    statusText.value = "";
    emit("verified", { accessToken: res.access_token });
  } catch {
    statusText.value = "验证失败或已过期，请重新发送验证邮件。";
  }
}

onMounted(() => {
  void tryVerifyFromToken();
});

onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer);
});
</script>

<style scoped>
.verify-card-glow {
  box-shadow: 0 0 50px -10px rgba(99, 102, 241, 0.3);
}
</style>
