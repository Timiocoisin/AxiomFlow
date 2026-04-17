<template>
  <main class="flex-grow container mx-auto px-4 py-8 max-w-7xl" id="main-content">
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">{{ t("documents.title") }}</h1>
        <p class="text-slate-500 mt-1">{{ t("documents.subtitle", { date: asOfDate }) }}</p>
      </div>
      <button
        class="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-xl font-semibold transition-all shadow-lg shadow-indigo-600/20"
        type="button"
        @click="$emit('new-translation')"
      >
        <Icon icon="ph:plus-bold" />
        {{ t("documents.newTranslation") }}
      </button>
    </div>

    <div class="glass relative z-30 rounded-2xl p-4 mb-6 flex flex-col md:flex-row gap-4 items-center">
      <div class="relative flex-grow w-full">
        <Icon class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-lg" icon="ph:magnifying-glass-bold" />
        <input
          v-model.trim="searchQuery"
          class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl py-2.5 pl-11 pr-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
          :placeholder="t('documents.searchPlaceholder')"
          type="text"
        />
      </div>
      <div class="grid grid-cols-2 gap-2 w-full md:flex md:w-auto">
        <div ref="statusMenuRef" class="relative min-w-0 md:min-w-[140px]">
          <button
            class="w-full flex items-center justify-between pl-4 pr-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/90 dark:bg-slate-900/80 text-slate-800 dark:text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-all shadow-sm text-left"
            type="button"
            @click="statusMenuOpen = !statusMenuOpen"
          >
            {{ statusFilterLabel }}
          </button>
          <Icon class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm" icon="ph:caret-down-bold" />
          <div
            v-if="statusMenuOpen"
            class="absolute z-[70] mt-2 w-full min-w-[160px] rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-xl overflow-hidden"
          >
            <button
              v-for="opt in statusOptions"
              :key="opt.value || 'all'"
              class="w-full text-left px-4 py-2.5 text-sm transition-colors hover:bg-indigo-50 dark:hover:bg-indigo-900/30"
              :class="statusFilter === opt.value ? 'bg-indigo-600 text-white hover:bg-indigo-600' : 'text-slate-700 dark:text-slate-200'"
              type="button"
              @click="pickStatus(opt.value)"
            >
              {{ opt.label }}
            </button>
          </div>
        </div>
        <div ref="timeMenuRef" class="relative min-w-0 md:min-w-[140px]">
          <button
            class="w-full flex items-center justify-between pl-4 pr-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/90 dark:bg-slate-900/80 text-slate-800 dark:text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-all shadow-sm text-left"
            type="button"
            @click="timeMenuOpen = !timeMenuOpen"
          >
            {{ timeFilterLabel }}
          </button>
          <Icon class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm" icon="ph:caret-down-bold" />
          <div
            v-if="timeMenuOpen"
            class="absolute z-[70] mt-2 w-full min-w-[160px] rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-xl overflow-hidden"
          >
            <button
              v-for="opt in timeOptions"
              :key="opt.value || 'all'"
              class="w-full text-left px-4 py-2.5 text-sm transition-colors hover:bg-indigo-50 dark:hover:bg-indigo-900/30"
              :class="timeFilter === opt.value ? 'bg-indigo-600 text-white hover:bg-indigo-600' : 'text-slate-700 dark:text-slate-200'"
              type="button"
              @click="pickTime(opt.value)"
            >
              {{ opt.label }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="glass relative z-10 rounded-2xl overflow-hidden shadow-xl border dark:border-slate-800">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-50/50 dark:bg-slate-900/50 border-b dark:border-slate-800">
              <th class="px-6 py-4 text-sm font-semibold text-slate-500">{{ t("documents.table.name") }}</th>
              <th class="px-6 py-4 text-sm font-semibold text-slate-500">{{ t("documents.table.uploadDate") }}</th>
              <th class="px-6 py-4 text-sm font-semibold text-slate-500">{{ t("documents.table.size") }}</th>
              <th class="px-6 py-4 text-sm font-semibold text-slate-500">{{ t("documents.table.langPair") }}</th>
              <th class="px-6 py-4 text-sm font-semibold text-slate-500">{{ t("documents.table.status") }}</th>
              <th class="px-6 py-4 text-sm font-semibold text-slate-500 text-right">{{ t("documents.table.actions") }}</th>
            </tr>
          </thead>
          <tbody class="divide-y dark:divide-slate-800">
            <tr v-if="docsLoading">
              <td class="px-6 py-6 text-sm text-slate-500" colspan="6">{{ t("documents.loading") }}</td>
            </tr>
            <tr v-else-if="filteredDocuments.length === 0">
              <td class="px-6 py-10" colspan="6">
                <div class="mx-auto max-w-md rounded-2xl border border-dashed border-slate-300/90 dark:border-slate-700 bg-slate-50/70 dark:bg-slate-900/40 px-6 py-10 text-center">
                  <div class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-100 text-indigo-600 dark:bg-indigo-900/40 dark:text-indigo-300">
                    <Icon class="text-2xl" icon="ph:folder-open-bold" />
                  </div>
                  <p class="text-base font-semibold text-slate-800 dark:text-slate-100">{{ t("documents.empty") }}</p>
                  <p class="mt-1 text-sm text-slate-500">{{ t("documents.emptyHint") }}</p>
                </div>
              </td>
            </tr>
            <tr v-for="row in pagedDocuments" v-else :key="row.id" class="hover:bg-slate-50/50 dark:hover:bg-slate-900/30 transition-colors">
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg flex items-center justify-center text-indigo-600">
                    <Icon class="text-2xl" icon="ph:file-pdf-bold" />
                  </div>
                  <div>
                    <p class="font-medium">{{ row.fileName }}</p>
                    <p class="text-xs text-slate-500">ID: {{ row.id }}</p>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 text-sm text-slate-500">{{ row.uploadTime }}</td>
              <td class="px-6 py-4 text-sm text-slate-500">{{ row.sizeText }}</td>
              <td class="px-6 py-4 text-sm text-slate-500">-</td>
              <td class="px-6 py-4">
                <span
                  class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold"
                  :class="row.statusClass"
                >
                  <span class="w-1.5 h-1.5 rounded-full" :class="row.statusDotClass"></span>
                  {{ row.statusText }}
                </span>
              </td>
              <td class="px-6 py-4 text-right">
                <div class="flex justify-end gap-2">
                  <button class="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 rounded-lg transition-all disabled:opacity-40 disabled:cursor-not-allowed" :title="row.hasOriginalFile ? t('documents.actions.comparePreview') : t('documents.sourceMissing')" type="button" :disabled="!row.hasOriginalFile" @click="$emit('open-preview', { id: row.id, fileName: row.fileName, mimeType: row.mimeType })">
                    <Icon class="text-xl" icon="ph:eye-bold" />
                  </button>
                  <button class="p-2 text-slate-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/30 rounded-lg transition-all disabled:opacity-40 disabled:cursor-not-allowed" :title="row.hasOriginalFile ? t('documents.actions.download') : t('documents.sourceMissing')" type="button" :disabled="!row.hasOriginalFile" @click="downloadDocument(row)">
                    <Icon class="text-xl" icon="ph:download-simple-bold" />
                  </button>
                  <button class="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-all disabled:opacity-40" :title="t('documents.actions.delete')" type="button" :disabled="deletingId === row.id" @click="deleteDocument(row)">
                    <Icon class="text-xl" icon="ph:trash-bold" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="px-6 py-4 bg-slate-50/50 dark:bg-slate-900/50 border-t dark:border-slate-800 flex items-center justify-between">
        <span class="text-sm text-slate-500">{{ t("documents.pagination.summary", { from: pageFrom, to: pageTo, total: filteredDocuments.length }) }}</span>
        <div v-if="filteredDocuments.length > pageSize" class="flex gap-2">
          <button
            class="px-3 py-1.5 rounded-lg border dark:border-slate-800 hover:bg-white dark:hover:bg-slate-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="currentPage <= 1"
            type="button"
            @click="goPrevPage"
          >
            <Icon icon="ph:caret-left-bold" />
          </button>
          <button
            v-for="pageNum in visiblePageNumbers"
            :key="pageNum"
            class="px-3 py-1.5 rounded-lg border dark:border-slate-800 hover:bg-white dark:hover:bg-slate-800 transition-colors"
            :class="pageNum === currentPage ? 'bg-indigo-600 text-white border-indigo-600 hover:bg-indigo-600 dark:hover:bg-indigo-600' : ''"
            type="button"
            @click="goPage(pageNum)"
          >
            {{ pageNum }}
          </button>
          <button
            class="px-3 py-1.5 rounded-lg border dark:border-slate-800 hover:bg-white dark:hover:bg-slate-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="currentPage >= totalPages"
            type="button"
            @click="goNextPage"
          >
            <Icon icon="ph:caret-right-bold" />
          </button>
        </div>
      </div>
    </div>

  </main>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { Icon } from "@iconify/vue";
import { deleteMyDocument, downloadMyDocument, getMyDocuments } from "./api/auth";

defineProps<{
  asOfDate: string;
}>();

defineEmits<{
  (e: "new-translation"): void;
  (e: "open-preview", payload: { id: string; fileName: string; mimeType: string }): void;
}>();

const { t } = useI18n();
const docsLoading = ref(false);
const searchQuery = ref("");
const statusFilter = ref("");
const timeFilter = ref("");
const statusMenuOpen = ref(false);
const timeMenuOpen = ref(false);
const statusMenuRef = ref<HTMLElement | null>(null);
const timeMenuRef = ref<HTMLElement | null>(null);
const deletingId = ref("");
const documents = ref<Array<{
  id: string;
  fileName: string;
  mimeType: string;
  hasOriginalFile: boolean;
  uploadTime: string;
  sizeText: string;
  statusText: string;
  statusRaw: string;
  wordCount: number;
  createdAtMs: number;
  statusClass: string;
  statusDotClass: string;
}>>([]);
const currentPage = ref(1);
const pageSize = 8;
const filteredDocuments = computed(() => {
  const q = searchQuery.value.toLowerCase();
  const now = Date.now();
  return documents.value.filter((row) => {
    if (q && !row.fileName.toLowerCase().includes(q) && !row.id.toLowerCase().includes(q)) return false;
    if (statusFilter.value && row.statusRaw !== statusFilter.value) return false;
    if (timeFilter.value === "today") return now - row.createdAtMs <= 24 * 60 * 60 * 1000;
    if (timeFilter.value === "week") return now - row.createdAtMs <= 7 * 24 * 60 * 60 * 1000;
    if (timeFilter.value === "month") return now - row.createdAtMs <= 30 * 24 * 60 * 60 * 1000;
    return true;
  });
});
const totalPages = computed(() => Math.max(1, Math.ceil(filteredDocuments.value.length / pageSize)));
const pagedDocuments = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return filteredDocuments.value.slice(start, start + pageSize);
});
const pageFrom = computed(() => (filteredDocuments.value.length === 0 ? 0 : (currentPage.value - 1) * pageSize + 1));
const pageTo = computed(() => (filteredDocuments.value.length === 0 ? 0 : Math.min(currentPage.value * pageSize, filteredDocuments.value.length)));
const statusOptions = computed(() => [
  { value: "", label: t("documents.filters.statusAll") },
  { value: "pending", label: t("documents.filters.statusPending") },
  { value: "processing", label: t("documents.filters.statusProcessing") },
  { value: "completed", label: t("documents.filters.statusCompleted") },
  { value: "failed", label: t("documents.filters.statusFailed") },
]);
const timeOptions = computed(() => [
  { value: "", label: t("documents.filters.timeAll") },
  { value: "today", label: t("documents.filters.timeToday") },
  { value: "week", label: t("documents.filters.timeWeek") },
  { value: "month", label: t("documents.filters.timeMonth") },
]);
const statusFilterLabel = computed(() => statusOptions.value.find((x) => x.value === statusFilter.value)?.label || t("documents.filters.statusAll"));
const timeFilterLabel = computed(() => timeOptions.value.find((x) => x.value === timeFilter.value)?.label || t("documents.filters.timeAll"));
const visiblePageNumbers = computed(() => {
  const pages: number[] = [];
  for (let i = 1; i <= totalPages.value; i += 1) pages.push(i);
  return pages;
});

function formatTimeText(v: string): string {
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return "-";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function formatSizeText(bytes: number): string {
  const n = Math.max(0, Number(bytes || 0));
  if (n <= 0) return "-";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

function mapStatusText(status: string): string {
  if (status === "failed") return t("documents.status.failed");
  if (status === "processing") return t("documents.filters.statusProcessing");
  if (status === "pending") return t("documents.filters.statusPending");
  return t("documents.status.completed");
}

function mapStatusClass(status: string): string {
  if (status === "failed") return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400";
  if (status === "processing") return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400";
  if (status === "pending") return "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400";
  return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400";
}

function mapStatusDotClass(status: string): string {
  if (status === "failed") return "bg-red-500";
  if (status === "processing") return "bg-blue-500 animate-pulse";
  if (status === "pending") return "bg-amber-500";
  return "bg-green-500 animate-pulse";
}

async function loadDocuments() {
  docsLoading.value = true;
  try {
    const rows = await getMyDocuments();
    documents.value = (Array.isArray(rows) ? rows : []).map((x) => ({
      id: String(x?.id || "-"),
      fileName: String(x?.file_name || t("profile.untitledDocument")),
      mimeType: String(x?.mime_type || "application/octet-stream"),
      hasOriginalFile: x?.has_original_file === false ? false : true,
      uploadTime: formatTimeText(String(x?.created_at || "")),
      sizeText: formatSizeText(Number(x?.file_size_bytes ?? 0)),
      statusText: mapStatusText(String(x?.status || "completed")),
      statusRaw: String(x?.status || "completed"),
      wordCount: Math.max(0, Number(x?.word_count ?? 0)),
      createdAtMs: new Date(String(x?.created_at || "")).getTime() || 0,
      statusClass: mapStatusClass(String(x?.status || "completed")),
      statusDotClass: mapStatusDotClass(String(x?.status || "completed")),
    }));
  } catch {
    documents.value = [];
  } finally {
    docsLoading.value = false;
  }
}

function goPage(pageNum: number) {
  currentPage.value = Math.min(totalPages.value, Math.max(1, pageNum));
}

function goPrevPage() {
  goPage(currentPage.value - 1);
}

function goNextPage() {
  goPage(currentPage.value + 1);
}

function pickStatus(v: string) {
  statusFilter.value = v;
  statusMenuOpen.value = false;
}

function pickTime(v: string) {
  timeFilter.value = v;
  timeMenuOpen.value = false;
}

async function downloadDocument(row: { id: string; fileName: string; uploadTime: string; sizeText: string; statusText: string; wordCount: number }) {
  try {
    const { blob, headers } = await downloadMyDocument(row.id, "original");
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const cd = String(headers?.["content-disposition"] || "");
    const match = cd.match(/filename\*=UTF-8''([^;]+)|filename="([^"]+)"/i);
    const parsed = decodeURIComponent((match?.[1] || match?.[2] || "").trim());
    a.download = parsed || row.fileName || "document.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch {
    window.alert(t("documents.downloadFailed"));
  }
}

async function deleteDocument(row: { id: string; fileName: string }) {
  const ok = window.confirm(t("documents.confirmDelete", { name: row.fileName }));
  if (!ok) return;
  deletingId.value = row.id;
  try {
    await deleteMyDocument(row.id);
    await loadDocuments();
  } finally {
    deletingId.value = "";
  }
}

onMounted(() => {
  void loadDocuments();
  document.addEventListener("mousedown", onDocClickOutside);
});

onBeforeUnmount(() => {
  document.removeEventListener("mousedown", onDocClickOutside);
});

watch(
  () => [documents.value.length, filteredDocuments.value.length],
  () => {
    if (currentPage.value > totalPages.value) currentPage.value = totalPages.value;
  },
);

watch([searchQuery, statusFilter, timeFilter], () => {
  currentPage.value = 1;
});

function onDocClickOutside(e: MouseEvent) {
  const target = e.target as Node | null;
  if (statusMenuRef.value && target && !statusMenuRef.value.contains(target)) statusMenuOpen.value = false;
  if (timeMenuRef.value && target && !timeMenuRef.value.contains(target)) timeMenuOpen.value = false;
}
</script>
