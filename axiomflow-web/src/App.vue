<template>
  <ResetPasswordPage
    v-if="page === 'reset-password'"
    :is-dark="isDark"
    @toggle-theme="toggleTheme"
    @done="page = 'auth'"
  />
  <AuthPage
    v-else-if="page === 'auth'"
    :is-dark="isDark"
    @toggle-theme="toggleTheme"
    @back="page = 'home'"
    @authed="handleAuthed"
    @verify-email="handleGoVerifyEmail"
  />
  <VerifyEmailPage
    v-else-if="page === 'verify-email'"
    :is-dark="isDark"
    :email="lastRegisterEmail"
    @toggle-theme="toggleTheme"
    @back="page = 'auth'"
    @verified="handleVerified"
  />
  <PreviewPage
    v-else-if="page === 'preview'"
    :service-time="serviceTime"
    @toggle-theme="toggleTheme"
    @back="page = 'documents'"
  />

  <template v-else>
  <div class="min-h-screen flex flex-col">
  <!-- Skip link -->
  <a class="sr-only focus:not-sr-only fixed top-4 left-4 z-[200] bg-indigo-600 text-white px-4 py-2 rounded-lg" href="#main-content">{{ $t("nav.skipNav") }}</a>
  <!-- Top progress bar -->
  <div class="progress-bar" id="loading-bar" :style="{ width: `${loadingBarWidth}%`, opacity: loadingBarOpacity }"></div>
  <!-- Offline banner -->
  <div class="bg-red-600 text-white text-center py-2 text-sm sticky top-0 z-[110]" id="offline-banner" :class="{ hidden: isOnline }">
    <div class="container mx-auto flex items-center justify-center gap-2">
      <Icon icon="ph:wifi-slash-bold" />
      {{ $t("nav.offlineBanner") }}
    </div>
  </div>
  <!-- Navbar -->
  <nav class="sticky top-0 z-50 glass border-b dark:border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16 items-center">
        <!-- Logo -->
        <div class="flex items-center gap-2">
          <img alt="Axiomflow Logo" class="w-8 h-8 rounded-lg" src="/icons/favicon.svg">
          <span class="text-xl font-bold tracking-tight">Axiomflow</span>
        </div>
        <!-- Menu -->
        <div class="hidden md:flex items-center space-x-8">
          <a
            class="text-sm font-medium transition-colors"
            :class="page === 'home' ? 'text-indigo-600' : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'"
            href="#"
            @click.prevent="page = 'home'"
          >{{ $t("nav.home") }}</a>
          <a
            class="text-sm font-medium transition-colors"
            :class="page === 'documents' ? 'text-indigo-600' : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'"
            href="#"
            @click.prevent="page = 'documents'"
          >{{ $t("nav.documents") }}</a>
        </div>
        <!-- Toolbar -->
        <div class="flex items-center gap-3">
          <!-- Language switch -->
          <div class="relative group">
            <button class="h-10 inline-flex items-center gap-1 text-sm font-medium px-3 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800">
              <Icon icon="ph:globe-bold" />
              <span>{{ uiLocale === "en-US" ? $t("nav.english") : $t("nav.chinese") }}</span>
            </button>
            <div class="absolute right-0 mt-2 w-40 bg-white dark:bg-slate-900 rounded-xl shadow-xl border dark:border-slate-800 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all p-2">
              <a
                class="block px-3 py-2 text-sm rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/30"
                href="#"
                @click.prevent="changeUiLocale('zh-CN')"
              >{{ $t("nav.chinese") }}</a>
              <a
                class="block px-3 py-2 text-sm rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/30"
                href="#"
                @click.prevent="changeUiLocale('en-US')"
              >{{ $t("nav.english") }}</a>
            </div>
          </div>
          <!-- Theme switch -->
          <button class="h-10 w-10 inline-flex items-center justify-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500" @click="toggleTheme">
            <Icon id="sun-icon" class="text-xl" icon="ph:sun-bold" :class="{ hidden: !isDark }" />
            <Icon id="moon-icon" class="text-xl" icon="ph:moon-bold" :class="{ hidden: isDark }" />
          </button>
          <button
            v-if="!isLoggedIn"
            class="h-10 inline-flex items-center justify-center px-5 rounded-xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-sm font-semibold hover:opacity-90 transition-opacity"
            @click.prevent="page = 'auth'"
          >
            {{ $t("nav.login") }}
          </button>
          <!-- User menu -->
          <div v-else class="relative group">
            <button class="flex items-center gap-2 p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
              <img
                alt="Avatar"
                class="w-8 h-8 rounded-full border border-slate-200 dark:border-slate-700"
                :src="avatarUrl"
                @error="handleAvatarLoadError"
              >
              <Icon class="text-xs text-slate-400" icon="ph:caret-down-bold" />
            </button>
            <div class="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-900 rounded-xl shadow-xl border dark:border-slate-800 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all p-2">
              <a class="flex items-center gap-2 px-3 py-2 text-sm rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800" href="#" @click.prevent="page = 'profile'">
                <Icon icon="ph:user-bold" /> {{ $t("nav.profile") }}
              </a>
              <a class="flex items-center gap-2 px-3 py-2 text-sm rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800" href="#" @click.prevent="page = 'settings'">
                <Icon icon="ph:gear-six-bold" /> {{ $t("nav.settings") }}
              </a>
              <div class="h-px bg-slate-100 dark:bg-slate-800 my-1"></div>
              <a class="flex items-center gap-2 px-3 py-2 text-sm rounded-lg text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30" href="#" @click.prevent="handleLogout">
                <Icon icon="ph:sign-out-bold" /> {{ $t("nav.logout") }}
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>

  </nav>
  <main v-if="page === 'home'" class="hero-gradient" id="main-content">
    <!-- Hero Section -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
      <div class="grid lg:grid-cols-2 gap-16 items-center">
        <div class="space-y-8">
          <div class="relative inline-flex">
            <span class="badge-breath absolute -inset-1 rounded-full bg-indigo-500/20 dark:bg-indigo-400/20"></span>
            <span class="relative inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 text-xs font-bold uppercase tracking-wider">
              <span class="flex h-2 w-2 rounded-full bg-indigo-600"></span>
              {{ t("home.badge") }}
            </span>
          </div>
          <h1 class="text-5xl lg:text-7xl font-extrabold leading-tight tracking-tight">
            {{ t("home.heroTitle") }}<br>
            <span class="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-500">{{ t("home.heroHighlight") }}</span>
          </h1>
          <p class="text-lg text-slate-600 dark:text-slate-400 max-w-xl leading-relaxed">
            {{ t("home.heroDesc") }}
          </p>
        </div>
        <!-- Upload entry -->
          <div class="relative group">
          <div class="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-3xl blur opacity-25 group-hover:opacity-40 transition duration-1000"></div>
          <div
            class="upload-breath upload-surface relative border-2 border-dashed p-10 lg:p-16 rounded-3xl text-center cursor-pointer hover:border-indigo-500 transition-all"
            id="drop-zone"
            @click="openModal"
            @dragover.prevent
            @drop.prevent="handleUploadDrop"
          >
            <div class="mb-6 inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 transition-transform group-hover:scale-110">
              <Icon class="text-4xl" icon="ph:cloud-arrow-up-bold" />
            </div>
            <h3 class="text-2xl font-bold mb-2">{{ t("home.uploadTitle") }}</h3>
            <p class="text-slate-500 mb-8">{{ t("home.uploadDesc") }}</p>
            <div class="flex justify-center gap-4 text-xs font-medium text-slate-400 uppercase tracking-widest">
              <span>{{ t("home.secure") }}</span>
              <span>•</span>
              <span>{{ t("home.e2e") }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
    <!-- Metrics -->
    <section class="max-w-7xl mx-auto px-4 pb-20">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-8">
        <div class="group p-6 rounded-3xl text-center card-surface card-surface-hover hover:-translate-y-1 transition-all duration-300">
          <div class="text-3xl font-extrabold tracking-tight text-indigo-600 group-hover:text-indigo-500 transition-colors">120+</div>
          <div class="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">{{ t("home.metricLanguages") }}</div>
        </div>
        <div class="group p-6 rounded-3xl text-center card-surface card-surface-hover hover:-translate-y-1 transition-all duration-300">
          <div class="text-3xl font-extrabold tracking-tight text-indigo-600 group-hover:text-indigo-500 transition-colors">2.5s</div>
          <div class="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">{{ t("home.metricSpeed") }}</div>
        </div>
        <div class="group p-6 rounded-3xl text-center card-surface card-surface-hover hover:-translate-y-1 transition-all duration-300">
          <div class="text-3xl font-extrabold tracking-tight text-indigo-600 group-hover:text-indigo-500 transition-colors">99.9%</div>
          <div class="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">{{ t("home.metricFidelity") }}</div>
        </div>
        <div class="group p-6 rounded-3xl text-center card-surface card-surface-hover hover:-translate-y-1 transition-all duration-300">
          <div class="text-3xl font-extrabold tracking-tight text-indigo-600 group-hover:text-indigo-500 transition-colors">5M+</div>
          <div class="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">{{ t("home.metricProcessed") }}</div>
        </div>
      </div>
    </section>
    <!-- Features -->
    <section class="py-24 section-surface">
      <div class="max-w-7xl mx-auto px-4">
        <div class="text-center mb-16 space-y-4">
          <h2 class="text-3xl md:text-5xl font-bold">{{ t("home.whyTitle") }}</h2>
          <p class="text-slate-500 max-w-2xl mx-auto">{{ t("home.whyDesc") }}</p>
        </div>
        <div class="grid md:grid-cols-3 gap-8">
          <!-- Feature 1 -->
          <div class="group p-8 rounded-3xl card-surface card-surface-hover hover:-translate-y-1 transition-all duration-300">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-100 to-violet-100 dark:from-indigo-500/20 dark:to-fuchsia-500/15 flex items-center justify-center text-indigo-600 mb-6 group-hover:scale-105 transition-transform">
              <Icon class="text-2xl" icon="ph:layout-bold" />
            </div>
            <h4 class="text-xl font-bold mb-3 tracking-tight">{{ t("home.f1Title") }}</h4>
            <p class="text-slate-600 dark:text-slate-400 leading-relaxed">{{ t("home.f1Desc") }}</p>
          </div>
          <!-- Feature 2 -->
          <div class="group p-8 rounded-3xl card-surface card-surface-hover hover:-translate-y-1 transition-all duration-300">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-100 to-violet-100 dark:from-indigo-500/20 dark:to-fuchsia-500/15 flex items-center justify-center text-indigo-600 mb-6 group-hover:scale-105 transition-transform">
              <Icon class="text-2xl" icon="ph:shield-check-bold" />
            </div>
            <h4 class="text-xl font-bold mb-3 tracking-tight">{{ t("home.f2Title") }}</h4>
            <p class="text-slate-600 dark:text-slate-400 leading-relaxed">{{ t("home.f2Desc") }}</p>
          </div>
          <!-- Feature 3 -->
          <div class="group p-8 rounded-3xl card-surface card-surface-hover hover:-translate-y-1 transition-all duration-300">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-100 to-violet-100 dark:from-indigo-500/20 dark:to-fuchsia-500/15 flex items-center justify-center text-indigo-600 mb-6 group-hover:scale-105 transition-transform">
              <Icon class="text-2xl" icon="ph:file-search-bold" />
            </div>
            <h4 class="text-xl font-bold mb-3 tracking-tight">{{ t("home.f3Title") }}</h4>
            <p class="text-slate-600 dark:text-slate-400 leading-relaxed">{{ t("home.f3Desc") }}</p>
          </div>
        </div>
      </div>
    </section>
  </main>
  <DocumentsPage
    v-else-if="page === 'documents'"
    :as-of-date="serviceDateCn"
    @new-translation="page = 'home'"
    @open-preview="page = 'preview'"
  />
  <ProfilePage
    v-else-if="page === 'profile'"
    :avatar-url="avatarUrl"
    @password-changed="onPasswordChanged"
    @avatar-updated="onAvatarUpdated"
    @account-deleted="onAccountDeleted"
  />
  <SettingsPage
    v-else-if="page === 'settings'"
    :service-time="serviceTime"
    :avatar-url="avatarUrl"
    @toggle-theme="toggleTheme"
    @password-changed="onPasswordChanged"
  />
  <!-- Preview modal (Mock) -->
  <div
    v-if="page === 'home'"
    class="fixed inset-0 z-[150] items-center justify-center px-4"
    id="preview-modal"
    :class="showPreview ? 'flex' : 'hidden'"
  >
    <div class="absolute inset-0 bg-slate-950/60 backdrop-blur-sm" @click="closeModal"></div>
    <div class="relative bg-white dark:bg-slate-900 w-full max-w-5xl rounded-3xl shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-300">
      <div class="p-4 border-b dark:border-slate-800 flex items-center justify-between">
        <h3 class="font-bold flex items-center gap-2">
          <Icon icon="ph:eye-bold" /> {{ t("home.previewTitle") }}
        </h3>
        <button class="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg" @click="closeModal">
          <Icon icon="ph:x-bold" />
        </button>
      </div>
      <div class="grid md:grid-cols-2 h-[60vh] overflow-hidden">
        <div class="border-r dark:border-slate-800 bg-slate-100 dark:bg-slate-800 p-8 overflow-y-auto">
          <div class="text-xs font-bold text-slate-400 mb-4 uppercase tracking-wider">{{ t("home.previewSource") }}</div>
          <img alt="Original PDF content with charts" class="w-full rounded shadow-md border" src="/icons/favicon.svg">
          <div class="mt-4 p-4 bg-white dark:bg-slate-900 rounded-lg space-y-2">
            <div class="h-4 w-3/4 bg-slate-200 dark:bg-slate-800 rounded"></div>
            <div class="h-4 w-1/2 bg-slate-200 dark:bg-slate-800 rounded"></div>
          </div>
        </div>
        <div class="p-8 overflow-y-auto">
          <div class="text-xs font-bold text-indigo-500 mb-4 uppercase tracking-wider">{{ t("home.previewTranslated") }}</div>
          <img alt="Translated PDF content with same layout" class="w-full rounded shadow-md border border-indigo-200" src="/icons/favicon.svg">
          <div class="mt-4 p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg space-y-2">
            <div class="h-4 w-3/4 bg-indigo-100 dark:bg-indigo-800/50 rounded"></div>
            <div class="h-4 w-1/2 bg-indigo-100 dark:bg-indigo-800/50 rounded"></div>
          </div>
        </div>
      </div>
      <div class="p-6 border-t dark:border-slate-800 flex justify-end gap-4">
        <button class="px-6 py-2 rounded-xl border dark:border-slate-700" @click="closeModal">{{ t("home.previewCancel") }}</button>
        <button class="px-6 py-2 rounded-xl bg-indigo-600 text-white font-bold" @click="startTranslation">{{ t("home.previewStart") }}</button>
      </div>
    </div>
  </div>
  <!-- Toast container -->
  <div v-if="page === 'home'" class="fixed bottom-8 right-8 z-[200] flex flex-col gap-3" id="toast-container">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="glass p-4 rounded-xl shadow-2xl flex items-center gap-3 animate-in slide-in-from-right-10 duration-300 min-w-[280px] border-l-4 border-l-indigo-600"
    >
      <Icon class="text-indigo-600 text-xl" icon="ph:info-bold" />
      <span class="text-sm font-medium">{{ toast.message }}</span>
      <button class="ml-auto text-slate-400 hover:text-slate-600" @click="removeToast(toast.id)">
        <Icon icon="ph:x-bold" />
      </button>
    </div>
  </div>
  <footer v-if="page === 'home'" class="section-surface pt-20 pb-10">
    <div class="max-w-7xl mx-auto px-4">
      <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-12 mb-20">
        <div class="col-span-2 lg:col-span-2">
          <div class="flex items-center gap-2 mb-6">
            <img alt="Axiomflow Logo" class="w-8 h-8 rounded-lg" src="/icons/favicon.svg">
            <span class="text-xl font-bold">Axiomflow</span>
          </div>
          <p class="text-slate-500 dark:text-slate-400 mb-8 max-w-sm">
            {{ t("home.footerDesc") }}
          </p>
          <div class="flex gap-4">
            <a class="w-10 h-10 rounded-full border dark:border-slate-800 flex items-center justify-center text-slate-400 hover:text-indigo-600 hover:border-indigo-600 transition-all" href="#">
              <Icon class="text-xl" icon="ph:twitter-logo-bold" />
            </a>
            <a class="w-10 h-10 rounded-full border dark:border-slate-800 flex items-center justify-center text-slate-400 hover:text-indigo-600 hover:border-indigo-600 transition-all" href="#">
              <Icon class="text-xl" icon="ph:github-logo-bold" />
            </a>
            <a class="w-10 h-10 rounded-full border dark:border-slate-800 flex items-center justify-center text-slate-400 hover:text-indigo-600 hover:border-indigo-600 transition-all" href="#">
              <Icon class="text-xl" icon="ph:linkedin-logo-bold" />
            </a>
          </div>
        </div>
        <div>
          <h5 class="font-bold mb-6 uppercase text-xs tracking-widest text-slate-400">{{ t("home.product") }}</h5>
          <ul class="space-y-4 text-sm font-medium text-slate-500">
            <li><a class="hover:text-indigo-600" href="#">{{ t("home.p1") }}</a></li>
            <li><a class="hover:text-indigo-600" href="#">{{ t("home.p2") }}</a></li>
            <li><a class="hover:text-indigo-600" href="#">{{ t("home.p3") }}</a></li>
            <li><a class="hover:text-indigo-600" href="#">{{ t("home.p4") }}</a></li>
          </ul>
        </div>
        <div>
          <h5 class="font-bold mb-6 uppercase text-xs tracking-widest text-slate-400">{{ t("home.resources") }}</h5>
          <ul class="space-y-4 text-sm font-medium text-slate-500">
            <li><a class="hover:text-indigo-600" href="#">{{ t("home.r1") }}</a></li>
            <li><a class="hover:text-indigo-600" href="#">{{ t("home.r2") }}</a></li>
            <li><a class="hover:text-indigo-600" href="#">{{ t("home.r3") }}</a></li>
            <li><a class="hover:text-indigo-600" href="#">{{ t("home.r4") }}</a></li>
          </ul>
        </div>
        <div>
          <h5 class="font-bold mb-6 uppercase text-xs tracking-widest text-slate-400">{{ t("home.compliance") }}</h5>
          <ul class="space-y-4 text-sm font-medium text-slate-500">
            <li><a class="hover:text-indigo-600" href="#">{{ t("home.c1") }}</a></li>
            <li><a class="hover:text-indigo-600" href="#">{{ t("home.c2") }}</a></li>
            <li><a class="hover:text-indigo-600" href="#">{{ t("home.c3") }}</a></li>
            <li><a class="hover:text-indigo-600" href="#">{{ t("home.c4") }}</a></li>
          </ul>
        </div>
      </div>
      <div class="pt-10 border-t dark:border-slate-800 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-slate-500">
        <p>© {{ currentYear }} Axiomflow. {{ t("home.rights") }}</p>
        <div class="flex items-center gap-6">
          <span class="flex items-center gap-2"><span class="status-light w-2.5 h-2.5 rounded-full"></span> {{ t("home.status") }}</span>
          <span>{{ t("home.serviceTime") }} {{ serviceTime }}</span>
        </div>
      </div>
    </div>
  </footer>
  <footer v-else class="mt-auto border-t dark:border-slate-800 py-8">
    <div class="max-w-7xl mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-3 text-sm text-slate-500">
      <p>© 2026 Axiomflow. {{ t("home.rights") }}</p>
      <div class="flex items-center gap-6">
        <span class="flex items-center gap-2"><span class="status-light w-2.5 h-2.5 rounded-full"></span> {{ t("home.status") }}</span>
        <span>{{ t("home.serviceTime") }} {{ serviceTime }}</span>
      </div>
    </div>
  </footer>
  </div>
  </template>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { Icon } from "@iconify/vue";
import axios from "axios";
import AuthPage from "./AuthPage.vue";
import DocumentsPage from "./DocumentsPage.vue";
import ProfilePage from "./ProfilePage.vue";
import SettingsPage from "./SettingsPage.vue";
import PreviewPage from "./PreviewPage.vue";
import ResetPasswordPage from "./ResetPasswordPage.vue";
import VerifyEmailPage from "./VerifyEmailPage.vue";
import { API_BASE_URL } from "./api/baseUrl";
import * as authApi from "./api/auth";
import { getLocale, setLocale, type UiLocale } from "./i18n";

type ToastItem = {
  id: number;
  message: string;
};

const DEFAULT_AVATAR_URL = "https://api.dicebear.com/7.x/avataaars/svg?seed=Felix";

const isDark = ref(false);
const isLoggedIn = ref(false);
const accessToken = ref<string>("");
const avatarUrl = ref<string>(sessionStorage.getItem("axiomflow:avatarUrl") || DEFAULT_AVATAR_URL);
const lastRegisterEmail = ref<string>(localStorage.getItem("axiomflow:lastRegisterEmail") || "");
const page = ref<
  "home" | "auth" | "documents" | "profile" | "settings" | "preview" | "verify-email" | "reset-password"
>("home");
const isOnline = ref(navigator.onLine);
const showPreview = ref(false);
const loadingBarWidth = ref(0);
const loadingBarOpacity = ref(1);
const toasts = ref<ToastItem[]>([]);
const now = ref(new Date());

let toastIdSeed = 0;

const { t } = useI18n();
const uiLocale = ref<UiLocale>(getLocale());
let loadingTimerA: number | null = null;
let loadingTimerB: number | null = null;
let clockTimer: number | null = null;
let themeSwitchTimer: number | null = null;
let accessRefreshTimer: number | null = null;
let oauthExchangeInFlight = false;
let shortcutsEnabled = true;

const currentYear = computed(() => now.value.getFullYear());
const serviceTime = computed(() => {
  const pad = (v: number) => String(v).padStart(2, "0");
  const y = now.value.getFullYear();
  const m = pad(now.value.getMonth() + 1);
  const d = pad(now.value.getDate());
  const hh = pad(now.value.getHours());
  const mm = pad(now.value.getMinutes());
  const ss = pad(now.value.getSeconds());
  return `${y}-${m}-${d} ${hh}:${mm}:${ss}`;
});
const serviceDateCn = computed(() => {
  const pad = (v: number) => String(v).padStart(2, "0");
  const y = now.value.getFullYear();
  const m = pad(now.value.getMonth() + 1);
  const d = pad(now.value.getDate());
  return uiLocale.value === "zh-CN" ? `${y}年${m}月${d}日` : `${y}-${m}-${d}`;
});

function updateThemeIcons() {
  const isDarkNow = document.body.classList.contains("theme-dark");
  isDark.value = isDarkNow;
}

function applyThemeClasses(dark: boolean) {
  document.documentElement.classList.toggle("dark", dark);
  document.body.classList.toggle("dark", dark);
  document.body.classList.toggle("theme-dark", dark);
  document.body.classList.toggle("theme-light", !dark);
}

function toggleTheme() {
  document.body.classList.add("theme-switching");
  if (themeSwitchTimer) window.clearTimeout(themeSwitchTimer);
  const nextDark = !document.body.classList.contains("theme-dark");
  applyThemeClasses(nextDark);
  updateThemeIcons();
  themeSwitchTimer = window.setTimeout(() => {
    document.body.classList.remove("theme-switching");
    themeSwitchTimer = null;
  }, 380);
}

function openModal() {
  if (!isLoggedIn.value) {
    page.value = "auth";
    showToast(t("toast.loginFirstToUpload"));
    return;
  }
  showPreview.value = true;
}

function handleUploadDrop(_e: DragEvent) {
  if (!isLoggedIn.value) {
    page.value = "auth";
    showToast(t("toast.loginFirstToUpload"));
    return;
  }
  openModal();
}

function closeModal() {
  showPreview.value = false;
}

function removeToast(id: number) {
  toasts.value = toasts.value.filter((t) => t.id !== id);
}

function showToast(message: string) {
  const id = ++toastIdSeed;
  toasts.value.push({ id, message });
  window.setTimeout(() => removeToast(id), 4000);
}

function oauthErrorMessage(code: string): string {
  switch (code) {
    case "invalid_oauth_state":
      return t("oauth.expired");
    case "missing_access_token":
      return t("oauth.missingAccessToken");
    case "github_email_unavailable":
      return t("oauth.githubEmailUnavailable");
    case "unsupported_oauth_provider":
      return t("oauth.unsupportedProvider");
    case "oauth_login_failed":
      return t("oauth.loginFailed");
    case "oauth_exchange_failed":
      return t("oauth.exchangeFailed");
    default:
      return t("oauth.unknown", { code: code || "unknown_error" });
  }
}

async function completeOauthLoginFromCookie() {
  if (oauthExchangeInFlight) return;
  oauthExchangeInFlight = true;
  try {
    const data = await authApi.refresh();
    handleAuthed({ accessToken: data.access_token, accessExpiresAt: data.access_expires_at });
    await syncAvatarFromApi();
    window.location.hash = "#/";
  } catch {
    showToast(oauthErrorMessage("oauth_exchange_failed"));
    page.value = "auth";
    window.location.hash = "#/auth";
  } finally {
    oauthExchangeInFlight = false;
  }
}

function tryShowBrowserNotification(title: string, body: string) {
  if (!("Notification" in window)) return;
  if (Notification.permission !== "granted") return;
  try {
    // Browser-level notification for users who enabled push preference.
    // eslint-disable-next-line no-new
    new Notification(title, { body, icon: "/icons/favicon.svg" });
  } catch {
    // ignore
  }
}

async function startTranslation() {
  showToast(t("toast.initTranslationEngine"));
  window.setTimeout(async () => {
    showToast(t("toast.uploadingAndAnalyzing"));
    if (isLoggedIn.value) {
      try {
        await authApi.notifyTranslationCompleted({
          title: "Annual_Report.pdf",
          document_count: 1,
          word_count: 1200,
        });
        const pref = await authApi.getNotificationPreferences();
        if (pref.notify_browser) {
          tryShowBrowserNotification(
            t("notification.translationCompletedTitle"),
            t("notification.translationCompletedBody", { title: "Annual_Report.pdf" }),
          );
        }
      } catch {
        // no-op for mock flow
      }
    }
    closeModal();
  }, 800);
}

function scheduleAccessTokenRefresh(expiresAt: string) {
  if (accessRefreshTimer) window.clearTimeout(accessRefreshTimer);
  const expMs = new Date(expiresAt).getTime();
  const delay = Math.max(5_000, expMs - Date.now() - 60_000);
  accessRefreshTimer = window.setTimeout(async () => {
    accessRefreshTimer = null;
    if (!sessionStorage.getItem("axiomflow:accessToken")) return;
    try {
      const { data } = await axios.post<{ access_token: string; access_expires_at?: string }>(
        `${API_BASE_URL}/auth/refresh`,
        {},
        { withCredentials: true, timeout: 15000 },
      );
      sessionStorage.setItem("axiomflow:accessToken", data.access_token);
      accessToken.value = data.access_token;
      if (data.access_expires_at) {
        sessionStorage.setItem("axiomflow:accessExpiresAt", data.access_expires_at);
        scheduleAccessTokenRefresh(data.access_expires_at);
      }
    } catch {
      /* session may be gone */
    }
  }, delay);
}

function handleAuthed(payload: { accessToken: string; accessExpiresAt?: string }) {
  isLoggedIn.value = true;
  accessToken.value = payload.accessToken;
  sessionStorage.setItem("axiomflow:accessToken", payload.accessToken);
  if (payload.accessExpiresAt) {
    sessionStorage.setItem("axiomflow:accessExpiresAt", payload.accessExpiresAt);
    scheduleAccessTokenRefresh(payload.accessExpiresAt);
  }
  void syncAvatarFromApi();
  void syncShortcutPreference();
  page.value = "home";
  showToast(t("toast.loginSuccess"));
}

function handleVerified(payload: { accessToken: string; accessExpiresAt?: string }) {
  isLoggedIn.value = true;
  accessToken.value = payload.accessToken;
  sessionStorage.setItem("axiomflow:accessToken", payload.accessToken);
  if (payload.accessExpiresAt) {
    sessionStorage.setItem("axiomflow:accessExpiresAt", payload.accessExpiresAt);
    scheduleAccessTokenRefresh(payload.accessExpiresAt);
  }
  void syncAvatarFromApi();
  void syncShortcutPreference();
  page.value = "home";
  showToast(t("toast.emailVerified"));
  window.location.hash = "#/";
}

function onPasswordChanged() {
  showToast(t("toast.passwordUpdated"));
}

function onAvatarUpdated(nextAvatar: string) {
  const normalized = normalizeAvatarUrl(nextAvatar);
  avatarUrl.value = normalized;
  if (normalized !== DEFAULT_AVATAR_URL) {
    sessionStorage.setItem("axiomflow:avatarUrl", normalized);
  } else {
    sessionStorage.removeItem("axiomflow:avatarUrl");
  }
  showToast(t("toast.avatarUpdated"));
}

function onAccountDeleted() {
  if (accessRefreshTimer) {
    window.clearTimeout(accessRefreshTimer);
    accessRefreshTimer = null;
  }
  isLoggedIn.value = false;
  accessToken.value = "";
  avatarUrl.value = DEFAULT_AVATAR_URL;
  sessionStorage.removeItem("axiomflow:accessToken");
  sessionStorage.removeItem("axiomflow:accessExpiresAt");
  sessionStorage.removeItem("axiomflow:avatarUrl");
  page.value = "auth";
  showToast(t("toast.accountDeleted"));
}

function normalizeAvatarUrl(raw: string | null | undefined): string {
  const v = (raw || "").trim();
  if (!v) return DEFAULT_AVATAR_URL;
  if (/^data:image\//i.test(v)) return v;
  if (/^https?:\/\//i.test(v)) return v;
  return DEFAULT_AVATAR_URL;
}

function handleAvatarLoadError() {
  avatarUrl.value = DEFAULT_AVATAR_URL;
  sessionStorage.removeItem("axiomflow:avatarUrl");
}

async function syncAvatarFromApi() {
  try {
    const me = await authApi.getMe();
    const normalized = normalizeAvatarUrl(me?.avatar_url || "");
    avatarUrl.value = normalized;
    if (normalized !== DEFAULT_AVATAR_URL) {
      sessionStorage.setItem("axiomflow:avatarUrl", normalized);
    } else {
      sessionStorage.removeItem("axiomflow:avatarUrl");
    }
  } catch {
    // keep current avatar
  }
}

function handleGoVerifyEmail(payload: { email: string }) {
  lastRegisterEmail.value = payload.email;
  page.value = "verify-email";
  showToast(t("toast.verificationEmailSent"));
}

function handleLogout() {
  if (accessRefreshTimer) {
    window.clearTimeout(accessRefreshTimer);
    accessRefreshTimer = null;
  }
  authApi
    .logout()
    .catch(() => {})
    .finally(() => {
      isLoggedIn.value = false;
      accessToken.value = "";
      avatarUrl.value = DEFAULT_AVATAR_URL;
      sessionStorage.removeItem("axiomflow:accessToken");
      sessionStorage.removeItem("axiomflow:accessExpiresAt");
      sessionStorage.removeItem("axiomflow:avatarUrl");
      page.value = "home";
      showToast(t("toast.loggedOut"));
    });
}

function handleOnline() {
  isOnline.value = true;
}

function handleOffline() {
  isOnline.value = false;
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === "Escape") closeModal();
  if (!shortcutsEnabled) return;

  const target = e.target as HTMLElement | null;
  const tag = (target?.tagName || "").toLowerCase();
  if (target?.isContentEditable || tag === "input" || tag === "textarea" || tag === "select") return;

  const key = (e.key || "").toLowerCase();
  const hasMod = e.ctrlKey || e.metaKey;
  if (e.altKey && key === "u") {
    e.preventDefault();
    quickUploadFromShortcut();
    return;
  }
  if (hasMod && key === "k") {
    e.preventDefault();
    page.value = "documents";
    showToast(t("toast.openedDocuments"));
  }
}

function quickUploadFromShortcut() {
  if (!isLoggedIn.value) {
    page.value = "auth";
    showToast(t("toast.loginFirstToUpload"));
    return;
  }
  page.value = "home";
}

async function syncShortcutPreference() {
  try {
    const pref = await authApi.getUserPreferences();
    shortcutsEnabled = Boolean(pref.enable_shortcuts);
    const next = pref.ui_language === "en-US" ? "en-US" : "zh-CN";
    uiLocale.value = next;
    setLocale(next);
  } catch {
    // keep default
  }
}

async function changeUiLocale(next: UiLocale) {
  uiLocale.value = next;
  setLocale(next);
  if (!isLoggedIn.value) return;
  try {
    const pref = await authApi.getUserPreferences();
    await authApi.updateUserPreferences({
      preferred_target_language: pref.preferred_target_language,
      ui_language: next,
      auto_save_history: Boolean(pref.auto_save_history),
      enable_shortcuts: Boolean(pref.enable_shortcuts),
    });
  } catch {
    // best-effort
  }
}

function handleLoad() {
  loadingBarWidth.value = 30;
  loadingTimerA = window.setTimeout(() => {
    loadingBarWidth.value = 100;
  }, 300);
  loadingTimerB = window.setTimeout(() => {
    loadingBarOpacity.value = 0;
  }, 600);
}

function getHashParams(): URLSearchParams {
  const hash = window.location.hash || "";
  const q = hash.indexOf("?");
  if (q < 0) return new URLSearchParams();
  return new URLSearchParams(hash.slice(q + 1));
}

function hashForPage(p: typeof page.value): string {
  switch (p) {
    case "auth":
      return "#/auth";
    case "verify-email":
      return "#/verify-email";
    case "reset-password":
      return "#/reset-password";
    case "documents":
      return "#/documents";
    case "profile":
      return "#/profile";
    case "settings":
      return "#/settings";
    case "preview":
      return "#/preview";
    default:
      return "#/";
  }
}

function syncPageFromHash() {
  const h = window.location.hash || "";
  if (h.startsWith("#/reset-password")) {
    page.value = "reset-password";
    return;
  }
  if (h.startsWith("#/verify-email")) {
    page.value = "verify-email";
    return;
  }
  if (h.startsWith("#/auth")) {
    const params = getHashParams();
    const oauthDone = params.get("oauth_done");
    const oauthErr = params.get("oauth_error");
    if (oauthDone === "1") {
      void completeOauthLoginFromCookie();
      return;
    }
    if (oauthErr) {
      showToast(oauthErrorMessage(oauthErr));
    }
    page.value = "auth";
    return;
  }
  if (h.startsWith("#/documents")) {
    page.value = "documents";
    return;
  }
  if (h.startsWith("#/profile")) {
    page.value = "profile";
    return;
  }
  if (h.startsWith("#/settings")) {
    page.value = "settings";
    return;
  }
  if (h.startsWith("#/preview")) {
    page.value = "preview";
    return;
  }
  page.value = "home";
}

watch(page, (p) => {
  const nextHash = hashForPage(p);
  if ((window.location.hash || "") !== nextHash) {
    window.location.hash = nextHash;
  }
});

onMounted(() => {
  // Avoid browser COOP "untrustworthy origin" warnings in local dev.
  // If opened via IP/127 on Vite dev server, normalize to localhost.
  if (window.location.protocol === "http:" && window.location.port === "5173" && window.location.hostname !== "localhost") {
    const next = `http://localhost:5173${window.location.pathname}${window.location.hash}`;
    window.location.replace(next);
    return;
  }

  applyThemeClasses(document.documentElement.classList.contains("dark"));
  updateThemeIcons();
  window.addEventListener("load", handleLoad);
  window.addEventListener("offline", handleOffline);
  window.addEventListener("online", handleOnline);
  document.addEventListener("keydown", handleKeydown);
  syncPageFromHash();
  window.addEventListener("hashchange", syncPageFromHash);
  clockTimer = window.setInterval(() => {
    now.value = new Date();
  }, 1000);
  if (document.readyState === "complete") handleLoad();

  // Try restore login state (best-effort). Refresh is cookie-based.
  const saved = sessionStorage.getItem("axiomflow:accessToken");
  if (saved) {
    accessToken.value = saved;
    isLoggedIn.value = true;
    const exp = sessionStorage.getItem("axiomflow:accessExpiresAt");
    if (exp) scheduleAccessTokenRefresh(exp);
    void syncAvatarFromApi();
    void syncShortcutPreference();
  }
  const savedAvatar = sessionStorage.getItem("axiomflow:avatarUrl");
  if (savedAvatar) {
    avatarUrl.value = normalizeAvatarUrl(savedAvatar);
  }
});

onBeforeUnmount(() => {
  window.removeEventListener("load", handleLoad);
  window.removeEventListener("offline", handleOffline);
  window.removeEventListener("online", handleOnline);
  document.removeEventListener("keydown", handleKeydown);
  window.removeEventListener("hashchange", syncPageFromHash);
  if (loadingTimerA) window.clearTimeout(loadingTimerA);
  if (loadingTimerB) window.clearTimeout(loadingTimerB);
  if (clockTimer) window.clearInterval(clockTimer);
  if (themeSwitchTimer) window.clearTimeout(themeSwitchTimer);
  if (accessRefreshTimer) window.clearTimeout(accessRefreshTimer);
});
</script>
