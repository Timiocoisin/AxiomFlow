<template>
  <main class="flex-grow container mx-auto px-4 py-10 max-w-5xl" id="main-content">
    <div class="flex flex-col md:flex-row gap-8">
      <aside class="hidden md:block w-64 space-y-2">
        <button
          v-for="item in tabs"
          :key="item.id"
          class="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all"
          :class="activeTab === item.id ? 'bg-white dark:bg-slate-800 shadow-md text-indigo-600' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800'"
          type="button"
          @click="activeTab = item.id"
        >
          <Icon class="text-xl" :icon="item.icon" />
          {{ item.label }}
        </button>
      </aside>

      <div class="flex-grow space-y-8">
        <div v-if="activeTab === 'basic'" class="glass rounded-3xl p-8">
          <h2 class="text-2xl font-bold mb-8">{{ t("profile.basicTitle") }}</h2>
          <div class="flex flex-col sm:flex-row items-center gap-8 mb-10">
            <div class="relative group">
              <img
                alt="Large Avatar"
                class="w-32 h-32 rounded-3xl border-4 border-white dark:border-slate-800 shadow-xl object-cover cursor-pointer"
                :src="avatarUrl"
                @click="openAvatarPicker"
              />
              <input
                ref="avatarInputRef"
                class="hidden"
                type="file"
                accept="image/png,image/jpeg,image/webp,image/gif"
                @change="onAvatarFileChange"
              />
              <button
                class="absolute -bottom-2 -right-2 w-10 h-10 bg-indigo-600 text-white rounded-xl flex items-center justify-center shadow-lg hover:scale-110 transition-transform"
                type="button"
                :disabled="avatarUploading"
                @click="openAvatarPicker"
              >
                <Icon icon="ph:camera-bold" />
              </button>
            </div>
            <div class="text-center sm:text-left space-y-1">
              <h3 class="text-xl font-bold">{{ profileUsername || t("profile.noUsername") }}</h3>
              <p class="text-slate-500 text-sm">{{ t("profile.registerDatePrefix") }}{{ registerDate }}</p>
              <p v-if="avatarMsg" class="text-sm" :class="avatarMsgType === 'error' ? 'text-rose-500' : 'text-emerald-500'">
                {{ avatarMsg }}
              </p>
              <div class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 text-xs font-bold mt-2">
                <Icon icon="ph:crown-bold" />
                {{ t("profile.proUser") }}
              </div>
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
              <label class="text-sm font-semibold text-slate-500 ml-1">{{ t("profile.usernameLabel") }}</label>
              <input
                class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                type="text"
                :value="profileUsername"
                readonly
              />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-semibold text-slate-500 ml-1">{{ t("profile.emailLabel") }}</label>
              <input
                class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                type="email"
                :value="profileEmail"
                readonly
              />
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'stats'" class="space-y-8">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="glass rounded-3xl p-6 border-l-4 border-l-indigo-600">
              <p class="text-slate-500 text-sm font-medium mb-1">{{ t("profile.translatedDocs") }}</p>
              <h3 class="text-3xl font-bold">{{ formatNumber(translatedDocuments) }}</h3>
              <p class="text-xs mt-2 flex items-center gap-1" :class="monthDeltaPct >= 0 ? 'text-green-500' : 'text-rose-500'">
                <Icon icon="ph:trend-up-bold" /> {{ t("profile.vsLastMonth") }} {{ monthDeltaPct >= 0 ? "+" : "" }}{{ monthDeltaPct }}%
              </p>
            </div>
            <div class="glass rounded-3xl p-6 border-l-4 border-l-purple-600">
              <p class="text-slate-500 text-sm font-medium mb-1">{{ t("profile.totalWords") }}</p>
              <h3 class="text-3xl font-bold">{{ formatNumber(translatedWords) }}</h3>
              <p class="text-xs text-slate-500 mt-2">{{ t("profile.savedHoursPrefix") }} {{ formatNumber(hoursSaved) }} {{ t("profile.savedHoursSuffix") }}</p>
            </div>
            <div class="glass rounded-3xl p-6 border-l-4 border-l-orange-600">
              <p class="text-slate-500 text-sm font-medium mb-1">{{ t("profile.creditsBalance") }}</p>
              <h3 class="text-3xl font-bold">{{ formatNumber(creditsBalance) }}</h3>
              <p class="text-xs text-indigo-600 mt-2 font-medium cursor-pointer hover:underline">{{ t("profile.topUpNow") }}</p>
            </div>
          </div>
          <div class="glass rounded-3xl p-8">
            <h2 class="text-xl font-bold mb-6">{{ t("profile.activityAnalytics") }}</h2>
            <div ref="activityChartRef" class="w-full h-80"></div>
          </div>

          <div class="glass rounded-3xl p-8">
            <h2 class="text-xl font-bold mb-6">{{ t("profile.recentActivities") }}</h2>
            <div v-if="statsLoading" class="text-sm text-slate-500">{{ t("profile.loading") }}</div>
            <div v-else-if="recentActivities.length === 0" class="text-sm text-slate-500">{{ t("profile.noActivity") }}</div>
            <div v-else class="space-y-6">
              <div v-for="item in recentActivities" :key="`${item.time}-${item.title}`" class="flex gap-4">
                <div class="w-10 h-10 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center text-indigo-600 flex-shrink-0">
                  <Icon class="text-xl" icon="ph:activity-bold" />
                </div>
                <div>
                  <p class="text-sm font-bold">{{ recentActivityTitle(item) }}</p>
                  <p class="text-xs text-slate-500">{{ formatTimeText(item.time) }} · {{ activityStatusLabel(item.status) }} · {{ recentActivityMeta(item) }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'security'" class="space-y-8">
          <div class="glass rounded-3xl p-8">
            <h2 class="text-2xl font-bold mb-8">{{ t("profile.changePasswordTitle") }}</h2>
            <form class="space-y-6 max-w-md" @submit.prevent="submitPasswordChange">
              <div class="space-y-2">
                <label class="text-sm font-semibold text-slate-500 ml-1">{{ t("profile.currentPassword") }}</label>
                <input
                  v-model="secCurrent"
                  class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                  placeholder="••••••••"
                  type="password"
                  autocomplete="current-password"
                />
              </div>
              <div class="space-y-2">
                <label class="text-sm font-semibold text-slate-500 ml-1">{{ t("profile.newPassword") }}</label>
                <input
                  v-model="secNew"
                  class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                  :placeholder="t('profile.newPasswordPlaceholder')"
                  type="password"
                  autocomplete="new-password"
                />
              </div>
              <div class="space-y-2">
                <label class="text-sm font-semibold text-slate-500 ml-1">{{ t("profile.confirmNewPassword") }}</label>
                <input
                  v-model="secNew2"
                  class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                  :placeholder="t('profile.confirmNewPasswordPlaceholder')"
                  type="password"
                  autocomplete="new-password"
                />
              </div>
              <p v-if="secMsg" class="text-sm text-rose-500">{{ secMsg }}</p>
              <button
                class="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-lg shadow-indigo-600/20 active:scale-95 disabled:opacity-60"
                type="submit"
                :disabled="secSubmitting"
              >
                {{ secSubmitting ? t("profile.submitting") : t("profile.updatePassword") }}
              </button>
            </form>
          </div>

          <div class="glass rounded-3xl p-8">
            <h2 class="text-xl font-bold mb-6">{{ t("profile.loginHistory") }}</h2>
            <div class="overflow-x-auto">
              <table class="w-full text-left text-sm">
                <thead>
                  <tr class="text-slate-500 border-b dark:border-slate-800">
                    <th class="pb-4 font-semibold">{{ t("profile.deviceBrowser") }}</th>
                    <th class="pb-4 font-semibold">{{ t("profile.ipAddress") }}</th>
                    <th class="pb-4 font-semibold">{{ t("profile.time") }}</th>
                    <th class="pb-4 font-semibold">{{ t("profile.status") }}</th>
                  </tr>
                </thead>
                <tbody v-if="displayLoginHistory.length > 0" class="divide-y dark:divide-slate-800">
                  <tr v-for="row in displayLoginHistory" :key="`${row.time}-${row.device}-${row.ip}`">
                    <td class="py-4 font-medium" :title="row.device">{{ row.device }}</td>
                    <td class="py-4 text-slate-500">{{ row.ip }}</td>
                    <td class="py-4 text-slate-500">{{ formatTimeText(row.time) }}</td>
                    <td class="py-4">
                      <span :class="row.status.startsWith('online') ? 'text-green-500 font-bold' : 'text-slate-500'">
                        {{
                          row.status === "online_current"
                            ? t("profile.currentDot")
                            : row.status === "online"
                              ? t("profile.onlineDot")
                              : t("profile.statusExpired")
                        }}
                      </span>
                    </td>
                  </tr>
                </tbody>
                <tbody v-else>
                  <tr>
                    <td class="py-4 text-slate-500" colspan="4">{{ t("profile.noLoginHistory") }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'notifications'" class="glass rounded-3xl p-8">
          <h2 class="text-2xl font-bold mb-8">{{ t("profile.notificationSettings") }}</h2>
          <div class="space-y-8">
            <div class="flex items-center justify-between">
              <div>
                <p class="font-bold">{{ t("profile.emailNotifications") }}</p>
                <p class="text-sm text-slate-500">{{ t("profile.emailNotificationsDesc") }}</p>
              </div>
              <button
                class="relative inline-block w-12 h-6 transition duration-200 ease-in-out rounded-full"
                :class="notifyEmail ? 'bg-indigo-600' : 'bg-slate-200 dark:bg-slate-800'"
                type="button"
                @click="notifyEmail = !notifyEmail"
              >
                <span class="absolute top-1 w-4 h-4 transition duration-200 ease-in-out bg-white rounded-full" :class="notifyEmail ? 'right-1' : 'left-1'"></span>
              </button>
            </div>
            <div class="flex items-center justify-between">
              <div>
                <p class="font-bold">{{ t("profile.browserPush") }}</p>
                <p class="text-sm text-slate-500">{{ t("profile.browserPushDesc") }}</p>
              </div>
              <button
                class="relative inline-block w-12 h-6 transition duration-200 ease-in-out rounded-full"
                :class="notifyBrowser ? 'bg-indigo-600' : 'bg-slate-200 dark:bg-slate-800'"
                type="button"
                @click="toggleBrowserNotify"
              >
                <span class="absolute top-1 w-4 h-4 transition duration-200 ease-in-out bg-white rounded-full" :class="notifyBrowser ? 'right-1' : 'left-1'"></span>
              </button>
            </div>
            <div class="flex items-center justify-between">
              <div>
                <p class="font-bold">{{ t("profile.marketing") }}</p>
                <p class="text-sm text-slate-500">{{ t("profile.marketingDesc") }}</p>
              </div>
              <button
                class="relative inline-block w-12 h-6 transition duration-200 ease-in-out rounded-full"
                :class="notifyMarketing ? 'bg-indigo-600' : 'bg-slate-200 dark:bg-slate-800'"
                type="button"
                @click="notifyMarketing = !notifyMarketing"
              >
                <span class="absolute top-1 w-4 h-4 transition duration-200 ease-in-out bg-white rounded-full" :class="notifyMarketing ? 'right-1' : 'left-1'"></span>
              </button>
            </div>
          </div>
          <div class="mt-10 pt-10 border-t dark:border-slate-800">
            <p v-if="notifyMsg" class="text-sm mb-4" :class="notifyMsgType === 'error' ? 'text-rose-500' : 'text-emerald-500'">
              {{ notifyMsg }}
            </p>
            <p v-else-if="notifyUpdatedAt" class="text-xs text-slate-500 mb-4">
              {{ t("profile.lastUpdatedPrefix") }}{{ formatTimeText(notifyUpdatedAt) }}
            </p>
            <button
              class="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-lg shadow-indigo-600/20 active:scale-95 disabled:opacity-60"
              type="button"
              :disabled="notifySaving"
              @click="saveNotificationPreferences"
            >
              {{ notifySaving ? t("common.saving") : t("profile.saveSettings") }}
            </button>
          </div>
        </div>

        <div v-else class="space-y-8">
          <div class="glass rounded-3xl p-8">
            <h2 class="text-xl font-bold mb-4">{{ t("profile.exportDataTitle") }}</h2>
            <p class="text-slate-500 text-sm mb-6">{{ t("profile.exportDataDesc") }}</p>
            <p v-if="exportMsg" class="text-sm mb-4" :class="exportMsgType === 'error' ? 'text-rose-500' : 'text-emerald-500'">
              {{ exportMsg }}
            </p>
            <button
              class="flex items-center gap-2 px-6 py-3 border-2 border-slate-200 dark:border-slate-800 rounded-xl font-bold hover:bg-slate-50 dark:hover:bg-slate-800 transition-all disabled:opacity-60"
              type="button"
              :disabled="exportingData"
              @click="handleExportData"
            >
              <Icon icon="ph:download-simple-bold" />
              {{ exportingData ? t("profile.exporting") : t("profile.exportData") }}
            </button>
          </div>
          <div class="bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30 rounded-3xl p-8">
            <h2 class="text-xl font-bold text-red-600 mb-4 flex items-center gap-2">
              <Icon icon="ph:warning-circle-bold" />
              {{ t("profile.dangerZone") }}
            </h2>
            <p class="text-red-700/70 dark:text-red-400/70 text-sm mb-6">{{ t("profile.dangerZoneDesc") }}</p>
            <div class="space-y-3 max-w-md">
              <input
                v-model="deletePassword"
                class="w-full bg-white/90 dark:bg-slate-900/40 border border-red-200 dark:border-red-900/40 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500/40 transition-all"
                type="password"
                autocomplete="current-password"
                :placeholder="t('profile.deletePasswordPlaceholder')"
              />
              <input
                v-model="deleteConfirmText"
                class="w-full bg-white/90 dark:bg-slate-900/40 border border-red-200 dark:border-red-900/40 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500/40 transition-all"
                type="text"
                :placeholder="t('profile.deleteConfirmPlaceholder')"
              />
              <p v-if="deleteMsg" class="text-sm" :class="deleteMsgType === 'error' ? 'text-rose-500' : 'text-emerald-500'">
                {{ deleteMsg }}
              </p>
              <button
                class="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-xl font-bold transition-all shadow-lg shadow-red-600/20 disabled:opacity-60"
                type="button"
                :disabled="deletingAccount"
                @click="openDeleteConfirm"
              >
                {{ deletingAccount ? t("profile.processing") : t("profile.deleteAccount") }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>

  <div
    v-if="showDeleteConfirmModal"
    class="fixed inset-0 z-[220] flex items-center justify-center px-4"
    @click.self="closeDeleteConfirm"
  >
    <div class="absolute inset-0 bg-slate-950/60 backdrop-blur-sm"></div>
    <div class="relative w-full max-w-md rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6">
      <h3 class="text-lg font-bold text-red-600 mb-2">{{ t("profile.deleteConfirmTitle") }}</h3>
      <p class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed mb-5">
        {{ t("profile.deleteConfirmDesc") }}
      </p>
      <div class="flex justify-end gap-3">
        <button
          class="px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
          type="button"
          @click="closeDeleteConfirm"
        >
          {{ t("profile.cancel") }}
        </button>
        <button
          class="px-4 py-2 rounded-xl bg-red-600 text-white font-semibold hover:bg-red-700 disabled:opacity-60"
          type="button"
          :disabled="deletingAccount"
          @click="confirmDeleteAccount"
        >
          {{ deletingAccount ? t("profile.processing") : t("profile.confirmDelete") }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { Icon } from "@iconify/vue";
import * as echarts from "echarts";
import * as authApi from "./api/auth";

const emit = defineEmits<{ (e: "password-changed"): void; (e: "avatar-updated", value: string): void; (e: "account-deleted"): void }>();
const { locale, t } = useI18n();
const props = defineProps<{ avatarUrl?: string }>();

type TabId = "basic" | "stats" | "security" | "notifications" | "actions";

const activeTab = ref<TabId>("basic");
const avatarUrl = computed(() => props.avatarUrl || "https://api.dicebear.com/7.x/avataaars/svg?seed=Felix");
const secCurrent = ref("");
const secNew = ref("");
const secNew2 = ref("");
const secMsg = ref("");
const secSubmitting = ref(false);
const notifyEmail = ref(true);
const notifyBrowser = ref(false);
const notifyMarketing = ref(false);
const notifySaving = ref(false);
const notifyMsg = ref("");
const notifyMsgType = ref<"error" | "success">("success");
const notifyUpdatedAt = ref("");
const exportingData = ref(false);
const exportMsg = ref("");
const exportMsgType = ref<"error" | "success">("success");
const deletingAccount = ref(false);
const deletePassword = ref("");
const deleteConfirmText = ref("");
const deleteMsg = ref("");
const deleteMsgType = ref<"error" | "success">("success");
const showDeleteConfirmModal = ref(false);
const activityChartRef = ref<HTMLElement | null>(null);
const avatarInputRef = ref<HTMLInputElement | null>(null);
const avatarUploading = ref(false);
const avatarMsg = ref("");
const avatarMsgType = ref<"error" | "success">("success");
const profileUsername = ref("");
const profileEmail = ref("");
const statsLoading = ref(false);
const translatedDocuments = ref(0);
const translatedWords = ref(0);
const creditsBalance = ref(0);
const monthDeltaPct = ref(0);
const hoursSaved = ref(0);
const activityChartData = ref<Array<{ date: string; count: number }>>([]);
type RecentActivityItem = {
  title: string;
  time: string;
  status: string;
  ip: string;
  activity_key?: string;
  document_count?: number;
  word_count?: number;
};

const recentActivities = ref<Array<RecentActivityItem>>([]);
const loginHistory = ref<Array<{ device: string; ip: string; time: string; status: string }>>([]);
let activityChart: echarts.ECharts | null = null;

const tabs = computed<Array<{ id: TabId; label: string; icon: string }>>(() => [
  { id: "basic", label: t("profile.tabBasic"), icon: "ph:user-circle-bold" },
  { id: "stats", label: t("profile.tabStats"), icon: "ph:chart-bar-bold" },
  { id: "security", label: t("profile.tabSecurity"), icon: "ph:shield-check-bold" },
  { id: "notifications", label: t("profile.tabNotifications"), icon: "ph:bell-bold" },
  { id: "actions", label: t("profile.tabMore"), icon: "ph:dots-three-circle-bold" },
]);

const registerDate = computed(() => {
  const d = new Date();
  const pad = (v: number) => String(v).padStart(2, "0");
  return locale.value === "zh-CN"
    ? `${d.getFullYear()}年${pad(d.getMonth() + 1)}月${pad(d.getDate())}日`
    : `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
});

function normalizeDeviceLabel(raw: string): string {
  const t = (raw || "").toLowerCase();
  if (!t) return "Unknown device";
  const browser = t.includes("edg/")
    ? "Edge"
    : t.includes("chrome/")
      ? "Chrome"
      : t.includes("firefox/")
        ? "Firefox"
        : t.includes("safari/") && !t.includes("chrome/")
          ? "Safari"
          : "Browser";
  const os = t.includes("windows")
    ? "Windows"
    : t.includes("mac os x") || t.includes("macintosh")
      ? "macOS"
      : t.includes("android")
        ? "Android"
        : t.includes("iphone") || t.includes("ipad") || t.includes("ios")
          ? "iOS"
          : t.includes("linux")
            ? "Linux"
            : "Unknown OS";
  return `${browser} on ${os}`;
}

const displayLoginHistory = computed(() => {
  const rows = [...loginHistory.value].sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime());
  const merged = new Map<string, { device: string; ip: string; time: string; status: string }>();
  for (const row of rows) {
    const device = normalizeDeviceLabel(row.device);
    const ip = row.ip || "-";
    const key = `${device}|${ip}`;
    if (!merged.has(key)) {
      merged.set(key, { ...row, device, ip });
    }
  }
  const compact = Array.from(merged.values()).slice(0, 5);
  let markedCurrent = false;
  return compact.map((row) => {
    if (!markedCurrent && row.status.startsWith("online")) {
      markedCurrent = true;
      return { ...row, status: "online_current" };
    }
    if (row.status === "online_current") return { ...row, status: "online" };
    return row;
  });
});

function openAvatarPicker() {
  if (avatarUploading.value) return;
  avatarInputRef.value?.click();
}

async function onAvatarFileChange(ev: Event) {
  const input = ev.target as HTMLInputElement | null;
  const file = input?.files?.[0];
  if (!file) return;
  avatarMsg.value = "";
  if (!file.type.startsWith("image/")) {
    avatarMsgType.value = "error";
    avatarMsg.value = t("profile.msgChooseImage");
    input.value = "";
    return;
  }
  const maxBytes = 1024 * 1024;
  if (file.size > maxBytes) {
    avatarMsgType.value = "error";
    avatarMsg.value = t("profile.msgImageTooLarge");
    input.value = "";
    return;
  }
  avatarUploading.value = true;
  try {
    const dataUrl = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ""));
      reader.onerror = () => reject(new Error("read_failed"));
      reader.readAsDataURL(file);
    });
    await authApi.updateAvatar({ avatar_url: dataUrl });
    try {
      const me = await authApi.getMe();
      emit("avatar-updated", String(me?.avatar_url || dataUrl));
    } catch {
      emit("avatar-updated", dataUrl);
    }
    avatarMsgType.value = "success";
    avatarMsg.value = t("profile.msgAvatarUpdated");
  } catch {
    avatarMsgType.value = "error";
    avatarMsg.value = t("profile.msgAvatarUpdateFailed");
  } finally {
    avatarUploading.value = false;
    input.value = "";
  }
}

async function submitPasswordChange() {
  secMsg.value = "";
  if (!sessionStorage.getItem("axiomflow:accessToken")) {
    secMsg.value = t("profile.msgLoginFirstForPassword");
    return;
  }
  if (secNew.value.length < 8 || !/[A-Za-z]/.test(secNew.value) || !/\d/.test(secNew.value)) {
    secMsg.value = t("profile.msgPasswordRule");
    return;
  }
  if (secNew.value !== secNew2.value) {
    secMsg.value = t("profile.msgPasswordMismatch");
    return;
  }
  secSubmitting.value = true;
  try {
    await authApi.changePassword({ current_password: secCurrent.value, new_password: secNew.value });
    secCurrent.value = "";
    secNew.value = "";
    secNew2.value = "";
    emit("password-changed");
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string }; status?: number } })?.response?.data?.detail;
    if (detail === "invalid_current_password") secMsg.value = t("profile.msgCurrentPasswordIncorrect");
    else secMsg.value = t("profile.msgPasswordUpdateFailed");
  } finally {
    secSubmitting.value = false;
  }
}

async function loadProfileMe() {
  try {
    const me = await authApi.getMe();
    profileUsername.value = String(me?.username || "");
    profileEmail.value = String(me?.email || "");
  } catch {
    profileUsername.value = "";
    profileEmail.value = "";
  }
}

function formatNumber(v: number): string {
  return new Intl.NumberFormat("zh-CN").format(Math.max(0, Number(v) || 0));
}

function formatTimeText(v: string): string {
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return "-";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function activityStatusLabel(status: string): string {
  if (status === "online") return t("profile.statusOnline");
  if (status === "expired") return t("profile.statusExpired");
  return t("profile.statusInfo");
}

function recentActivityTitle(item: RecentActivityItem): string {
  if (item.activity_key === "translation_completed") {
    return (item.title || t("profile.untitledDocument")).trim();
  }
  if (item.activity_key === "password_reset_requested") return t("profile.activityPasswordResetRequested");
  if (item.activity_key === "email_verified") return t("profile.activityEmailVerified");
  if (item.activity_key === "login_succeeded") return t("profile.activityLoginSucceeded");
  return item.title || "-";
}

function recentActivityMeta(item: RecentActivityItem): string {
  if (item.activity_key === "translation_completed") {
    const docs = Math.max(0, Number(item.document_count ?? 0));
    const words = Math.max(0, Number(item.word_count ?? 0));
    return t("profile.activityTranslateMeta", { docs, words });
  }
  return item.ip || "-";
}

async function loadProfileStats() {
  statsLoading.value = true;
  try {
    const stats = await authApi.getProfileStats();
    translatedDocuments.value = Number(stats?.metrics?.translated_documents || 0);
    translatedWords.value = Number(stats?.metrics?.translated_words || 0);
    creditsBalance.value = Number(stats?.metrics?.credits_balance || 0);
    monthDeltaPct.value = Number(stats?.metrics?.month_delta_pct || 0);
    hoursSaved.value = Number(stats?.metrics?.hours_saved || 0);
    activityChartData.value = Array.isArray(stats?.activity_chart) ? stats.activity_chart : [];
    recentActivities.value = Array.isArray(stats?.recent_activities) ? stats.recent_activities : [];
    loginHistory.value = Array.isArray(stats?.login_history) ? stats.login_history : [];
  } catch {
    translatedDocuments.value = 0;
    translatedWords.value = 0;
    creditsBalance.value = 0;
    monthDeltaPct.value = 0;
    hoursSaved.value = 0;
    activityChartData.value = [];
    recentActivities.value = [];
    loginHistory.value = [];
  } finally {
    statsLoading.value = false;
  }
}

async function loadNotificationPreferences() {
  notifyMsg.value = "";
  try {
    const pref = await authApi.getNotificationPreferences();
    notifyEmail.value = Boolean(pref.notify_email);
    notifyBrowser.value = Boolean(pref.notify_browser);
    if ("Notification" in window && Notification.permission === "denied") {
      notifyBrowser.value = false;
    }
    notifyMarketing.value = Boolean(pref.notify_marketing);
    notifyUpdatedAt.value = String(pref.updated_at || "");
  } catch {
    notifyMsgType.value = "error";
    notifyMsg.value = t("profile.msgNotifyLoadFailed");
  }
}

async function toggleBrowserNotify() {
  notifyMsg.value = "";
  if (!notifyBrowser.value) {
    if (!("Notification" in window)) {
      notifyMsgType.value = "error";
      notifyMsg.value = t("profile.msgBrowserNotSupported");
      return;
    }
    if (Notification.permission === "default") {
      const granted = await Notification.requestPermission();
      if (granted !== "granted") {
        notifyMsgType.value = "error";
        notifyMsg.value = t("profile.msgBrowserPermissionDenied");
        notifyBrowser.value = false;
        return;
      }
    }
    if (Notification.permission !== "granted") {
      notifyMsgType.value = "error";
      notifyMsg.value = t("profile.msgBrowserPermissionDenied");
      notifyBrowser.value = false;
      return;
    }
    notifyBrowser.value = true;
    return;
  }
  notifyBrowser.value = false;
}

async function saveNotificationPreferences() {
  notifySaving.value = true;
  notifyMsg.value = "";
  try {
    const pref = await authApi.updateNotificationPreferences({
      notify_email: notifyEmail.value,
      notify_browser: notifyBrowser.value,
      notify_marketing: notifyMarketing.value,
    });
    notifyUpdatedAt.value = String(pref.updated_at || "");
    notifyMsgType.value = "success";
    notifyMsg.value = t("profile.msgNotifySaved");
  } catch {
    notifyMsgType.value = "error";
    notifyMsg.value = t("profile.msgNotifySaveFailed");
  } finally {
    notifySaving.value = false;
  }
}

async function handleExportData() {
  exportingData.value = true;
  exportMsg.value = "";
  try {
    const data = await authApi.exportMyData();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const d = new Date();
    const pad = (n: number) => String(n).padStart(2, "0");
    const name = `axiomflow-export-${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}.json`;
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    exportMsgType.value = "success";
    exportMsg.value = t("profile.msgExportSuccess");
  } catch {
    exportMsgType.value = "error";
    exportMsg.value = t("profile.msgExportFailed");
  } finally {
    exportingData.value = false;
  }
}

async function handleDeleteAccount() {
  deleteMsg.value = "";
  if (!deletePassword.value) {
    deleteMsgType.value = "error";
    deleteMsg.value = t("profile.msgDeleteNeedPassword");
    return;
  }
  if ((deleteConfirmText.value || "").trim().toUpperCase() !== "DELETE") {
    deleteMsgType.value = "error";
    deleteMsg.value = t("profile.msgDeleteNeedConfirm");
    return;
  }
  deletingAccount.value = true;
  try {
    await authApi.deleteMyAccount({
      current_password: deletePassword.value,
      confirm_text: deleteConfirmText.value,
    });
    deleteMsgType.value = "success";
    deleteMsg.value = t("profile.msgDeleteSuccess");
    showDeleteConfirmModal.value = false;
    emit("account-deleted");
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
    if (detail === "invalid_current_password") {
      deleteMsgType.value = "error";
      deleteMsg.value = t("profile.msgCurrentPasswordIncorrect");
    } else if (detail === "invalid_confirm_text") {
      deleteMsgType.value = "error";
      deleteMsg.value = t("profile.msgDeleteConfirmWrong");
    } else {
      deleteMsgType.value = "error";
      deleteMsg.value = t("profile.msgDeleteFailed");
    }
  } finally {
    deletingAccount.value = false;
  }
}

function openDeleteConfirm() {
  deleteMsg.value = "";
  showDeleteConfirmModal.value = true;
}

function closeDeleteConfirm() {
  if (deletingAccount.value) return;
  showDeleteConfirmModal.value = false;
}

function confirmDeleteAccount() {
  void handleDeleteAccount();
}

function renderActivityChart() {
  if (!activityChartRef.value) return;
  if (activityChart && activityChart.getDom() !== activityChartRef.value) {
    activityChart.dispose();
    activityChart = null;
  }
  if (!activityChart) {
    activityChart = echarts.init(activityChartRef.value);
  }
  const isDark = document.body.classList.contains("theme-dark");
  activityChart.setOption({
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "line",
        lineStyle: {
          color: isDark ? "rgba(148,163,184,0.7)" : "rgba(100,116,139,0.45)",
          type: "dashed",
        },
      },
      backgroundColor: isDark ? "rgba(15,23,42,0.92)" : "rgba(255,255,255,0.96)",
      borderColor: isDark ? "rgba(148,163,184,0.3)" : "rgba(148,163,184,0.35)",
      borderWidth: 1,
      textStyle: {
        color: isDark ? "#e2e8f0" : "#0f172a",
      },
    },
    grid: {
      left: "5%",
      right: "3%",
      top: "8%",
      bottom: "10%",
      containLabel: true,
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: activityChartData.value.map((x) => x.date),
      axisLine: { lineStyle: { color: isDark ? "#334155" : "#e2e8f0" } },
      axisLabel: { color: isDark ? "#94a3b8" : "#94a3b8" },
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 10,
      splitNumber: 5,
      axisLabel: { color: isDark ? "#94a3b8" : "#64748b" },
      axisLine: { show: false },
      splitLine: {
        lineStyle: {
          color: isDark ? "rgba(148,163,184,0.18)" : "#e2e8f0",
        },
      },
    },
    series: [
      {
        name: t("profile.chartSeriesName"),
        type: "line",
        smooth: true,
        data: activityChartData.value.map((x) => Number(x.count || 0)),
        symbol: "circle",
        symbolSize: 7,
        itemStyle: {
          color: "#6366f1",
          borderColor: "#6366f1",
          borderWidth: 2,
        },
        lineStyle: {
          color: "#6366f1",
          width: 3,
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(99, 102, 241, 0.20)" },
            { offset: 1, color: "rgba(99, 102, 241, 0)" },
          ]),
        },
      },
    ],
  });
}

function handleResize() {
  activityChart?.resize();
}

onMounted(() => {
  void loadProfileMe();
  void loadProfileStats();
  void loadNotificationPreferences();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  activityChart?.dispose();
  activityChart = null;
});

watch(
  activeTab,
  async (tab) => {
    if (tab !== "stats") return;
    await nextTick();
    renderActivityChart();
    activityChart?.resize();
  },
  { immediate: true },
);

watch(activityChartData, async () => {
  if (activeTab.value !== "stats") return;
  await nextTick();
  renderActivityChart();
  activityChart?.resize();
});
</script>
