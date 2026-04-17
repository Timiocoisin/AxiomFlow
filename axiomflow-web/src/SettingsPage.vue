<template>
  <main class="flex-grow container mx-auto px-4 py-8 max-w-5xl" id="main-content">
    <div class="flex flex-col md:flex-row gap-8">
      <aside class="w-full md:w-64 space-y-2">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-left transition-all"
          :class="
            activeTab === tab.id
              ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 font-semibold'
              : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400'
          "
          type="button"
          @click="activeTab = tab.id"
        >
          <Icon :icon="tab.icon" />
          {{ tab.label }}
        </button>
      </aside>

      <div class="flex-grow">
        <div class="glass rounded-2xl p-6 md:p-8 border dark:border-slate-800">
          <section v-if="activeTab === 'preferences'" class="space-y-6">
            <h2 class="text-2xl font-bold">{{ t("settings.preferences.title") }}</h2>
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h4 class="font-semibold">{{ t("settings.preferences.targetLangTitle") }}</h4>
                <p class="text-sm text-slate-500">{{ t("settings.preferences.targetLangDesc") }}</p>
              </div>
              <div class="relative w-full md:w-52">
                <button
                  class="w-full flex items-center justify-between pl-4 pr-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/90 dark:bg-slate-900/80 text-slate-800 dark:text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-all shadow-sm"
                  type="button"
                  @click="toggleTargetDropdown"
                >
                  <span>{{ languageLabel(preferredTargetLanguage) }}</span>
                  <Icon icon="ph:caret-down-bold" class="text-slate-400 text-sm" />
                </button>
                <div
                  v-if="showTargetDropdown"
                  class="absolute z-30 mt-2 w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-xl overflow-hidden"
                >
                  <button
                    v-for="opt in languageOptions"
                    :key="`target-${opt.value}`"
                    class="w-full text-left px-4 py-2.5 text-sm transition-colors hover:bg-indigo-50 dark:hover:bg-indigo-900/30"
                    :class="preferredTargetLanguage === opt.value ? 'bg-indigo-600 text-white hover:bg-indigo-600' : 'text-slate-700 dark:text-slate-200'"
                    type="button"
                    @click="selectTargetLanguage(opt.value)"
                  >
                    {{ opt.label }}
                  </button>
                </div>
              </div>
            </div>
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h4 class="font-semibold">{{ t("settings.preferences.uiLangTitle") }}</h4>
                <p class="text-sm text-slate-500">{{ t("settings.preferences.uiLangDesc") }}</p>
              </div>
              <div class="relative w-full md:w-52">
                <button
                  class="w-full flex items-center justify-between pl-4 pr-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/90 dark:bg-slate-900/80 text-slate-800 dark:text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-all shadow-sm"
                  type="button"
                  @click="toggleUiDropdown"
                >
                  <span>{{ languageLabel(uiLanguage) }}</span>
                  <Icon icon="ph:caret-down-bold" class="text-slate-400 text-sm" />
                </button>
                <div
                  v-if="showUiDropdown"
                  class="absolute z-30 mt-2 w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-xl overflow-hidden"
                >
                  <button
                    v-for="opt in languageOptions"
                    :key="`ui-${opt.value}`"
                    class="w-full text-left px-4 py-2.5 text-sm transition-colors hover:bg-indigo-50 dark:hover:bg-indigo-900/30"
                    :class="uiLanguage === opt.value ? 'bg-indigo-600 text-white hover:bg-indigo-600' : 'text-slate-700 dark:text-slate-200'"
                    type="button"
                    @click="selectUiLanguage(opt.value)"
                  >
                    {{ opt.label }}
                  </button>
                </div>
              </div>
            </div>
            <div class="flex items-center justify-between py-2">
              <div>
                <h4 class="font-semibold">{{ t("settings.preferences.autoSaveTitle") }}</h4>
                <p class="text-sm text-slate-500">{{ t("settings.preferences.autoSaveDesc") }}</p>
              </div>
              <button class="relative inline-block w-11 h-6 rounded-full transition-colors" :class="autoSaveHistory ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-slate-700'" type="button" @click="autoSaveHistory = !autoSaveHistory">
                <span class="absolute top-[2px] h-5 w-5 rounded-full bg-white transition-all" :class="autoSaveHistory ? 'left-[22px]' : 'left-[2px]'"></span>
              </button>
            </div>
            <div class="pt-4 border-t dark:border-slate-800">
              <p v-if="prefMsg" class="text-sm mb-3" :class="prefMsgType === 'error' ? 'text-rose-500' : 'text-emerald-500'">
                {{ prefMsg }}
              </p>
              <p v-else-if="prefUpdatedAt" class="text-xs text-slate-500 mb-3">{{ t("settings.preferences.updatedAt", { time: formatTime(prefUpdatedAt) }) }}</p>
              <button
                class="px-6 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-bold hover:bg-indigo-700 disabled:opacity-60"
                type="button"
                :disabled="prefSaving || prefLoading"
                @click="savePreferences"
              >
                {{ prefSaving ? t("common.saving") : t("settings.preferences.saveBtn") }}
              </button>
            </div>
            <div class="pt-6 border-t dark:border-slate-800 space-y-4">
              <h4 class="font-semibold">{{ t("settings.preferences.shortcutsTitle") }}</h4>
              <div class="flex items-center justify-between py-1">
                <div>
                  <p class="text-sm font-medium">{{ t("settings.preferences.shortcutsEnableTitle") }}</p>
                  <p class="text-xs text-slate-500">{{ t("settings.preferences.shortcutsEnableDesc") }}</p>
                </div>
                <button
                  class="relative inline-block w-11 h-6 rounded-full transition-colors"
                  :class="enableShortcuts ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-slate-700'"
                  type="button"
                  @click="enableShortcuts = !enableShortcuts"
                >
                  <span class="absolute top-[2px] h-5 w-5 rounded-full bg-white transition-all" :class="enableShortcuts ? 'left-[22px]' : 'left-[2px]'"></span>
                </button>
              </div>
              <div class="grid grid-cols-1 gap-2">
                <div class="flex justify-between items-center text-sm p-3 rounded-lg bg-slate-100 dark:bg-slate-800">
                  <span>{{ t("settings.preferences.shortcutUpload") }}</span>
                  <kbd class="px-2 py-1 bg-white dark:bg-slate-900 border dark:border-slate-700 rounded shadow-sm font-sans">{{ uploadShortcutLabel }}</kbd>
                </div>
                <div class="flex justify-between items-center text-sm p-3 rounded-lg bg-slate-100 dark:bg-slate-800">
                  <span>{{ t("settings.preferences.shortcutSearch") }}</span>
                  <kbd class="px-2 py-1 bg-white dark:bg-slate-900 border dark:border-slate-700 rounded shadow-sm font-sans">{{ searchShortcutLabel }}</kbd>
                </div>
              </div>
            </div>
          </section>

          <section v-else-if="activeTab === 'upload'" class="space-y-6">
            <h2 class="text-2xl font-bold">{{ t("settings.upload.title") }}</h2>
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h4 class="font-semibold">{{ t("settings.upload.uploadSizeTitle") }}</h4>
                <p class="text-sm text-slate-500">{{ t("settings.upload.uploadSizeDesc") }}</p>
              </div>
              <div class="relative w-full md:w-52">
                <button
                  class="w-full flex items-center justify-between pl-4 pr-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/90 dark:bg-slate-900/80 text-slate-800 dark:text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-all shadow-sm"
                  type="button"
                  @click="toggleUploadSizeDropdown"
                >
                  <span>{{ uploadSizeLabel(uploadSizeLimitMb) }}</span>
                  <Icon icon="ph:caret-down-bold" class="text-slate-400 text-sm" />
                </button>
                <div
                  v-if="showUploadSizeDropdown"
                  class="absolute z-30 mt-2 w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-xl overflow-hidden"
                >
                  <button
                    v-for="size in uploadSizeOptions"
                    :key="`size-${size}`"
                    class="w-full text-left px-4 py-2.5 text-sm transition-colors hover:bg-indigo-50 dark:hover:bg-indigo-900/30"
                    :class="uploadSizeLimitMb === size ? 'bg-indigo-600 text-white hover:bg-indigo-600' : 'text-slate-700 dark:text-slate-200'"
                    type="button"
                    @click="selectUploadSize(size)"
                  >
                    {{ uploadSizeLabel(size) }}
                  </button>
                </div>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <div class="w-full border-t dark:border-slate-800"></div>
            </div>
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h4 class="font-semibold">{{ t("settings.upload.outputTitle") }}</h4>
                <p class="text-sm text-slate-500">{{ t("settings.upload.outputDesc") }}</p>
              </div>
              <div class="flex gap-2">
                <button
                  class="px-3 py-1.5 rounded-lg text-xs font-bold transition-colors"
                  :class="defaultOutputFormat === 'pdf' ? 'border-2 border-indigo-600 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600' : 'border dark:border-slate-800 text-slate-500'"
                  type="button"
                  @click="defaultOutputFormat = 'pdf'"
                >
                  PDF
                </button>
                <button
                  class="px-3 py-1.5 rounded-lg text-xs font-bold transition-colors"
                  :class="defaultOutputFormat === 'docx' ? 'border-2 border-indigo-600 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600' : 'border dark:border-slate-800 text-slate-500'"
                  type="button"
                  @click="defaultOutputFormat = 'docx'"
                >
                  DOCX
                </button>
                <button
                  class="px-3 py-1.5 rounded-lg text-xs font-bold transition-colors"
                  :class="defaultOutputFormat === 'txt' ? 'border-2 border-indigo-600 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600' : 'border dark:border-slate-800 text-slate-500'"
                  type="button"
                  @click="defaultOutputFormat = 'txt'"
                >
                  TXT
                </button>
              </div>
            </div>
            <div class="pt-4 border-t dark:border-slate-800">
              <p v-if="uploadMsg" class="text-sm mb-3" :class="uploadMsgType === 'error' ? 'text-rose-500' : 'text-emerald-500'">
                {{ uploadMsg }}
              </p>
              <p v-else-if="uploadUpdatedAt" class="text-xs text-slate-500 mb-3">{{ t("settings.upload.updatedAt", { time: formatTime(uploadUpdatedAt) }) }}</p>
              <button
                class="px-6 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-bold hover:bg-indigo-700 disabled:opacity-60"
                type="button"
                :disabled="uploadSaving || uploadLoading"
                @click="saveUploadOutputPreferences"
              >
                {{ uploadSaving ? t("common.saving") : t("settings.upload.saveBtn") }}
              </button>
            </div>
          </section>

          <section v-else class="space-y-8">
            <h2 class="text-2xl font-bold">{{ t("settings.privacy.title") }}</h2>
            <div>
              <h4 class="font-semibold mb-2">{{ t("settings.privacy.retentionTitle") }}</h4>
              <p class="text-sm text-slate-500 mb-4">{{ t("settings.privacy.retentionDesc") }}</p>
              <div class="relative w-full md:w-72">
                <button
                  class="w-full flex items-center justify-between pl-4 pr-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/90 dark:bg-slate-900/80 text-slate-800 dark:text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-all shadow-sm"
                  type="button"
                  @click="toggleRetentionDropdown"
                >
                  <span>{{ retentionLabel(dataRetentionDays) }}</span>
                  <Icon icon="ph:caret-down-bold" class="text-slate-400 text-sm" />
                </button>
                <div
                  v-if="showRetentionDropdown"
                  class="absolute z-30 mt-2 w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-xl overflow-hidden"
                >
                  <button
                    v-for="opt in retentionOptions"
                    :key="`ret-${opt.value}`"
                    class="w-full text-left px-4 py-2.5 text-sm transition-colors hover:bg-indigo-50 dark:hover:bg-indigo-900/30"
                    :class="dataRetentionDays === opt.value ? 'bg-indigo-600 text-white hover:bg-indigo-600' : 'text-slate-700 dark:text-slate-200'"
                    type="button"
                    @click="selectRetention(opt.value)"
                  >
                    {{ opt.label }}
                  </button>
                </div>
              </div>
              <div class="pt-4">
                <p v-if="privacyMsg" class="text-sm mb-3" :class="privacyMsgType === 'error' ? 'text-rose-500' : 'text-emerald-500'">
                  {{ privacyMsg }}
                </p>
                <p v-else-if="privacyUpdatedAt" class="text-xs text-slate-500 mb-3">{{ t("settings.privacy.updatedAt", { time: formatTime(privacyUpdatedAt) }) }}</p>
                <button
                  class="px-6 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-bold hover:bg-indigo-700 disabled:opacity-60"
                  type="button"
                  :disabled="privacySaving || privacyLoading"
                  @click="savePrivacySettings"
                >
                  {{ privacySaving ? t("common.saving") : t("settings.privacy.saveBtn") }}
                </button>
              </div>
            </div>
            <div class="pt-6 border-t dark:border-slate-800">
              <h4 class="font-semibold mb-4">{{ t("settings.privacy.apiKeysTitle") }}</h4>
              <p v-if="apiKeyMsg" class="text-sm mb-3" :class="apiKeyMsgType === 'error' ? 'text-rose-500' : 'text-emerald-500'">
                {{ apiKeyMsg }}
              </p>
              <div
                v-if="newApiKeyRaw"
                class="mb-4 p-4 rounded-xl border border-emerald-200 dark:border-emerald-900/40 bg-emerald-50/70 dark:bg-emerald-900/20"
              >
                <p class="text-sm font-semibold text-emerald-700 dark:text-emerald-300 mb-1">{{ t("settings.privacy.apiKeyNewOnce") }}</p>
                <div class="flex items-center justify-between gap-2">
                  <code class="text-xs md:text-sm break-all text-emerald-700 dark:text-emerald-200">{{ newApiKeyRaw }}</code>
                  <button
                    class="px-3 py-1 rounded-lg text-xs font-bold border border-emerald-300 dark:border-emerald-800 text-emerald-700 dark:text-emerald-200 hover:bg-emerald-100/70 dark:hover:bg-emerald-900/30"
                    type="button"
                    @click="copyNewApiKey"
                  >
                    {{ t("common.copy") }}
                  </button>
                </div>
              </div>
              <div v-if="apiKeys.length === 0" class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-dashed dark:border-slate-700">
                <p class="text-sm text-slate-500">{{ t("settings.privacy.apiKeysEmpty") }}</p>
              </div>
              <div v-else class="space-y-3">
                <div
                  v-for="item in apiKeys"
                  :key="item.id"
                  class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-dashed dark:border-slate-700"
                >
                  <div class="flex flex-wrap items-center justify-between gap-2 mb-2">
                    <span class="text-xs font-mono text-slate-500 dark:text-slate-300">{{ item.masked_key }}</span>
                    <button
                      class="text-rose-500 text-sm font-medium disabled:opacity-50"
                      type="button"
                      :disabled="Boolean(item.revoked_at) || apiKeyRevokingId === item.id"
                      @click="revokeApiKeyItem(item.id)"
                    >
                      {{ item.revoked_at ? t("settings.privacy.revoked") : apiKeyRevokingId === item.id ? t("settings.privacy.revoking") : t("settings.privacy.revoke") }}
                    </button>
                  </div>
                  <p class="text-xs text-slate-500">
                    {{ t("settings.privacy.createdAt", { time: formatTime(item.created_at) }) }}
                    <span v-if="item.last_used_at"> · {{ t("settings.privacy.lastUsedAt", { time: formatTime(item.last_used_at) }) }}</span>
                  </p>
                </div>
              </div>
              <button class="mt-4 text-sm font-bold text-indigo-600 flex items-center gap-1 disabled:opacity-60" type="button" :disabled="apiKeyCreating || apiKeyLoading" @click="createApiKeyItem">
                <Icon icon="ph:plus-bold" />
                {{ apiKeyCreating ? t("settings.privacy.creatingKey") : t("settings.privacy.createKey") }}
              </button>
              <p class="text-xs text-slate-500 mt-3">{{ t("settings.privacy.apiKeyHint") }}</p>
            </div>
          </section>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { Icon } from "@iconify/vue";
import * as authApi from "./api/auth";
import { setLocale } from "./i18n";

const props = defineProps<{
  serviceTime: string;
  avatarUrl?: string;
}>();

const emit = defineEmits<{
  (e: "toggle-theme"): void;
}>();

type SettingsTab = "preferences" | "upload" | "privacy";

const { t } = useI18n();
const tabs = computed<Array<{ id: SettingsTab; label: string; icon: string }>>(() => [
  { id: "preferences", label: t("settings.tabs.preferences"), icon: "ph:gear-six-bold" },
  { id: "upload", label: t("settings.tabs.upload"), icon: "ph:cloud-arrow-up-bold" },
  { id: "privacy", label: t("settings.tabs.privacy"), icon: "ph:shield-check-bold" },
]);

const activeTab = ref<SettingsTab>("preferences");
const autoSaveHistory = ref(true);
const preferredTargetLanguage = ref<"zh-CN" | "en-US">("zh-CN");
const uiLanguage = ref<"zh-CN" | "en-US">("zh-CN");
const showTargetDropdown = ref(false);
const showUiDropdown = ref(false);
const prefLoading = ref(false);
const prefSaving = ref(false);
const prefMsg = ref("");
const prefMsgType = ref<"error" | "success">("success");
const prefUpdatedAt = ref("");
const enableShortcuts = ref(true);
const uploadLoading = ref(false);
const uploadSaving = ref(false);
const uploadMsg = ref("");
const uploadMsgType = ref<"error" | "success">("success");
const uploadUpdatedAt = ref("");
const uploadSizeLimitMb = ref<20 | 50 | 100>(20);
const showUploadSizeDropdown = ref(false);
const uploadSizeOptions: Array<20 | 50 | 100> = [20, 50, 100];
const defaultOutputFormat = ref<"pdf" | "docx" | "txt">("pdf");
const privacyLoading = ref(false);
const privacySaving = ref(false);
const privacyMsg = ref("");
const privacyMsgType = ref<"error" | "success">("success");
const privacyUpdatedAt = ref("");
const showRetentionDropdown = ref(false);
const dataRetentionDays = ref<-1 | 0 | 1 | 7 | 30>(7);
const retentionOptions = computed<Array<{ value: -1 | 0 | 1 | 7 | 30; label: string }>>(() => [
  { value: 0, label: t("settings.privacy.retention.deleteNow") },
  { value: 1, label: t("settings.privacy.retention.delete1d") },
  { value: 7, label: t("settings.privacy.retention.delete7d") },
  { value: 30, label: t("settings.privacy.retention.delete30d") },
  { value: -1, label: t("settings.privacy.retention.keepForever") },
]);
const apiKeyLoading = ref(false);
const apiKeyCreating = ref(false);
const apiKeyRevokingId = ref("");
const apiKeyMsg = ref("");
const apiKeyMsgType = ref<"error" | "success">("success");
const apiKeys = ref<authApi.ApiKeyItem[]>([]);
const newApiKeyRaw = ref("");
const languageOptions = computed<Array<{ value: "zh-CN" | "en-US"; label: string }>>(() => [
  { value: "zh-CN", label: t("nav.chinese") },
  { value: "en-US", label: t("nav.english") },
]);
const isMac = typeof navigator !== "undefined" && /Mac|iPhone|iPad|iPod/.test(navigator.platform || "");
const uploadShortcutLabel = isMac ? "Option + U" : "Alt + U";
const searchShortcutLabel = isMac ? "⌘ + K" : "Ctrl + K";

function languageLabel(v: "zh-CN" | "en-US"): string {
  return languageOptions.value.find((x) => x.value === v)?.label || v;
}

function toggleTargetDropdown() {
  showTargetDropdown.value = !showTargetDropdown.value;
  if (showTargetDropdown.value) showUiDropdown.value = false;
}

function toggleUiDropdown() {
  showUiDropdown.value = !showUiDropdown.value;
  if (showUiDropdown.value) showTargetDropdown.value = false;
}

function toggleUploadSizeDropdown() {
  showUploadSizeDropdown.value = !showUploadSizeDropdown.value;
  if (showUploadSizeDropdown.value) {
    showTargetDropdown.value = false;
    showUiDropdown.value = false;
  }
}

function selectTargetLanguage(v: "zh-CN" | "en-US") {
  preferredTargetLanguage.value = v;
  showTargetDropdown.value = false;
}

function selectUiLanguage(v: "zh-CN" | "en-US") {
  uiLanguage.value = v;
  showUiDropdown.value = false;
  setLocale(v);
}

function uploadSizeLabel(v: 20 | 50 | 100): string {
  if (v === 20) return `20 MB (${t("settings.upload.recommended")})`;
  return `${v} MB`;
}

function retentionLabel(v: -1 | 0 | 1 | 7 | 30): string {
  return retentionOptions.value.find((x) => x.value === v)?.label || t("settings.privacy.retention.delete7d");
}

function selectUploadSize(v: 20 | 50 | 100) {
  uploadSizeLimitMb.value = v;
  showUploadSizeDropdown.value = false;
}

function toggleRetentionDropdown() {
  showRetentionDropdown.value = !showRetentionDropdown.value;
  if (showRetentionDropdown.value) {
    showTargetDropdown.value = false;
    showUiDropdown.value = false;
    showUploadSizeDropdown.value = false;
  }
}

function selectRetention(v: -1 | 0 | 1 | 7 | 30) {
  dataRetentionDays.value = v;
  showRetentionDropdown.value = false;
}

function handleDocClick(ev: MouseEvent) {
  const target = ev.target as HTMLElement | null;
  if (!target?.closest(".relative")) {
    showTargetDropdown.value = false;
    showUiDropdown.value = false;
    showUploadSizeDropdown.value = false;
    showRetentionDropdown.value = false;
  }
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "-";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

async function loadPreferences() {
  prefLoading.value = true;
  prefMsg.value = "";
  try {
    const data = await authApi.getUserPreferences();
    preferredTargetLanguage.value = data.preferred_target_language === "en-US" ? "en-US" : "zh-CN";
    uiLanguage.value = data.ui_language === "en-US" ? "en-US" : "zh-CN";
    setLocale(uiLanguage.value);
    autoSaveHistory.value = Boolean(data.auto_save_history);
    enableShortcuts.value = Boolean(data.enable_shortcuts);
    prefUpdatedAt.value = String(data.updated_at || "");
  } catch {
    prefMsgType.value = "error";
    prefMsg.value = t("settings.preferences.loadFailed");
  } finally {
    prefLoading.value = false;
  }
}

async function savePreferences() {
  prefSaving.value = true;
  prefMsg.value = "";
  try {
    const data = await authApi.updateUserPreferences({
      preferred_target_language: preferredTargetLanguage.value,
      ui_language: uiLanguage.value,
      auto_save_history: autoSaveHistory.value,
      enable_shortcuts: enableShortcuts.value,
    });
    prefUpdatedAt.value = String(data.updated_at || "");
    prefMsgType.value = "success";
    prefMsg.value = t("settings.preferences.saved");
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
    prefMsgType.value = "error";
    prefMsg.value = detail === "invalid_language_code" ? t("settings.preferences.invalidLang") : t("settings.preferences.saveFailed");
  } finally {
    prefSaving.value = false;
  }
}

async function loadUploadOutputPreferences() {
  uploadLoading.value = true;
  uploadMsg.value = "";
  try {
    const data = await authApi.getUploadOutputPreferences();
    uploadSizeLimitMb.value = data.upload_size_limit_mb === 50 ? 50 : data.upload_size_limit_mb === 100 ? 100 : 20;
    defaultOutputFormat.value =
      data.default_output_format === "docx" ? "docx" : data.default_output_format === "txt" ? "txt" : "pdf";
    uploadUpdatedAt.value = String(data.updated_at || "");
  } catch {
    uploadMsgType.value = "error";
    uploadMsg.value = t("settings.upload.loadFailed");
  } finally {
    uploadLoading.value = false;
  }
}

async function saveUploadOutputPreferences() {
  uploadSaving.value = true;
  uploadMsg.value = "";
  try {
    const data = await authApi.updateUploadOutputPreferences({
      upload_size_limit_mb: uploadSizeLimitMb.value,
      auto_import_provider: "none",
      default_output_format: defaultOutputFormat.value,
    });
    uploadUpdatedAt.value = String(data.updated_at || "");
    uploadMsgType.value = "success";
    uploadMsg.value = t("settings.upload.saved");
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
    uploadMsgType.value = "error";
    uploadMsg.value =
      detail === "invalid_upload_size_limit" || detail === "invalid_auto_import_provider" || detail === "invalid_default_output_format"
        ? t("settings.upload.invalid")
        : t("settings.upload.saveFailed");
  } finally {
    uploadSaving.value = false;
  }
}

async function loadPrivacySettings() {
  privacyLoading.value = true;
  privacyMsg.value = "";
  try {
    const data = await authApi.getPrivacySettings();
    dataRetentionDays.value =
      data.data_retention_days === -1 || data.data_retention_days === 0 || data.data_retention_days === 1 || data.data_retention_days === 30
        ? data.data_retention_days
        : 7;
    privacyUpdatedAt.value = String(data.updated_at || "");
  } catch {
    privacyMsgType.value = "error";
    privacyMsg.value = t("settings.privacy.loadFailed");
  } finally {
    privacyLoading.value = false;
  }
}

async function savePrivacySettings() {
  privacySaving.value = true;
  privacyMsg.value = "";
  try {
    const data = await authApi.updatePrivacySettings({ data_retention_days: dataRetentionDays.value });
    privacyUpdatedAt.value = String(data.updated_at || "");
    privacyMsgType.value = "success";
    privacyMsg.value = t("settings.privacy.saved");
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
    privacyMsgType.value = "error";
    privacyMsg.value = detail === "invalid_data_retention_days" ? t("settings.privacy.invalidRetention") : t("settings.privacy.saveFailed");
  } finally {
    privacySaving.value = false;
  }
}

async function loadApiKeys() {
  apiKeyLoading.value = true;
  apiKeyMsg.value = "";
  try {
    apiKeys.value = await authApi.listApiKeys();
  } catch {
    apiKeyMsgType.value = "error";
    apiKeyMsg.value = t("settings.privacy.apiKeyListFailed");
  } finally {
    apiKeyLoading.value = false;
  }
}

async function createApiKeyItem() {
  apiKeyCreating.value = true;
  apiKeyMsg.value = "";
  try {
    const data = await authApi.createApiKey();
    newApiKeyRaw.value = data.raw_key;
    apiKeyMsgType.value = "success";
    apiKeyMsg.value = t("settings.privacy.apiKeyCreated");
    await loadApiKeys();
  } catch {
    apiKeyMsgType.value = "error";
    apiKeyMsg.value = t("settings.privacy.apiKeyCreateFailed");
  } finally {
    apiKeyCreating.value = false;
  }
}

async function revokeApiKeyItem(id: string) {
  apiKeyRevokingId.value = id;
  apiKeyMsg.value = "";
  try {
    await authApi.revokeApiKey(id);
    apiKeyMsgType.value = "success";
    apiKeyMsg.value = t("settings.privacy.apiKeyRevoked");
    await loadApiKeys();
  } catch {
    apiKeyMsgType.value = "error";
    apiKeyMsg.value = t("settings.privacy.apiKeyRevokeFailed");
  } finally {
    apiKeyRevokingId.value = "";
  }
}

async function copyNewApiKey() {
  const text = newApiKeyRaw.value.trim();
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    apiKeyMsgType.value = "success";
    apiKeyMsg.value = t("common.copied");
  } catch {
    apiKeyMsgType.value = "error";
    apiKeyMsg.value = t("common.copyFailed");
  }
}

onMounted(() => {
  void loadPreferences();
  void loadUploadOutputPreferences();
  void loadPrivacySettings();
  void loadApiKeys();
  document.addEventListener("click", handleDocClick);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleDocClick);
});
</script>
