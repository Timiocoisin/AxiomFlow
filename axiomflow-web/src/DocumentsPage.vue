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

    <div class="glass rounded-2xl p-4 mb-6 flex flex-col md:flex-row gap-4 items-center">
      <div class="relative flex-grow w-full">
        <Icon class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-lg" icon="ph:magnifying-glass-bold" />
        <input
          class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl py-2.5 pl-11 pr-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
          :placeholder="t('documents.searchPlaceholder')"
          type="text"
        />
      </div>
      <div class="flex gap-2 w-full md:w-auto">
        <select class="bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl py-2.5 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all flex-grow md:flex-none">
          <option value="">{{ t("documents.filters.statusAll") }}</option>
          <option value="pending">{{ t("documents.filters.statusPending") }}</option>
          <option value="processing">{{ t("documents.filters.statusProcessing") }}</option>
          <option value="completed">{{ t("documents.filters.statusCompleted") }}</option>
          <option value="failed">{{ t("documents.filters.statusFailed") }}</option>
        </select>
        <select class="bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl py-2.5 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all flex-grow md:flex-none">
          <option value="">{{ t("documents.filters.timeAll") }}</option>
          <option value="today">{{ t("documents.filters.timeToday") }}</option>
          <option value="week">{{ t("documents.filters.timeWeek") }}</option>
          <option value="month">{{ t("documents.filters.timeMonth") }}</option>
        </select>
      </div>
    </div>

    <div class="glass rounded-2xl overflow-hidden shadow-xl border dark:border-slate-800">
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
            <tr v-else-if="documents.length === 0">
              <td class="px-6 py-6 text-sm text-slate-500" colspan="6">{{ t("documents.empty") }}</td>
            </tr>
            <tr v-for="row in documents" v-else :key="row.id" class="hover:bg-slate-50/50 dark:hover:bg-slate-900/30 transition-colors">
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
              <td class="px-6 py-4 text-sm text-slate-500">{{ t("documents.table.words", { count: row.wordCount }) }}</td>
              <td class="px-6 py-4 text-sm text-slate-500">-</td>
              <td class="px-6 py-4">
                <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                  <span class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                  {{ t("documents.status.completed") }}
                </span>
              </td>
              <td class="px-6 py-4 text-right">
                <div class="flex justify-end gap-2">
                  <button class="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 rounded-lg transition-all" :title="t('documents.actions.comparePreview')" type="button" @click="$emit('open-preview')">
                    <Icon class="text-xl" icon="ph:layout-bold" />
                  </button>
                  <button class="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 rounded-lg transition-all" :title="t('documents.actions.viewDetails')" type="button" @click="openDetails(row.fileName)">
                    <Icon class="text-xl" icon="ph:eye-bold" />
                  </button>
                  <button class="p-2 text-slate-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/30 rounded-lg transition-all" :title="t('documents.actions.download')" type="button">
                    <Icon class="text-xl" icon="ph:download-simple-bold" />
                  </button>
                  <button class="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-all" :title="t('documents.actions.delete')" type="button">
                    <Icon class="text-xl" icon="ph:trash-bold" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="px-6 py-4 bg-slate-50/50 dark:bg-slate-900/50 border-t dark:border-slate-800 flex items-center justify-between">
        <span class="text-sm text-slate-500">{{ t("documents.pagination.summary", { from: documents.length > 0 ? 1 : 0, to: documents.length, total: documents.length }) }}</span>
        <div class="flex gap-2">
          <button class="px-3 py-1.5 rounded-lg border dark:border-slate-800 hover:bg-white dark:hover:bg-slate-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed" disabled type="button">
            <Icon icon="ph:caret-left-bold" />
          </button>
          <button class="px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-medium" type="button">1</button>
          <button class="px-3 py-1.5 rounded-lg border dark:border-slate-800 hover:bg-white dark:hover:bg-slate-800 transition-colors" type="button">2</button>
          <button class="px-3 py-1.5 rounded-lg border dark:border-slate-800 hover:bg-white dark:hover:bg-slate-800 transition-colors" type="button">3</button>
          <button class="px-3 py-1.5 rounded-lg border dark:border-slate-800 hover:bg-white dark:hover:bg-slate-800 transition-colors" type="button">
            <Icon icon="ph:caret-right-bold" />
          </button>
        </div>
      </div>
    </div>

    <div class="fixed inset-0 z-[100] p-4" :class="showDetails ? 'flex items-center justify-center' : 'hidden'">
      <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" @click="closeDetails"></div>
      <div class="relative glass w-full max-w-4xl max-h-[90vh] rounded-3xl overflow-hidden flex flex-col shadow-2xl">
        <div class="p-6 border-b dark:border-slate-800 flex justify-between items-center">
          <div>
            <h2 class="text-xl font-bold">{{ modalTitle }}</h2>
            <p class="text-sm text-slate-500">{{ t("documents.modal.compareHint") }}</p>
          </div>
          <button class="w-10 h-10 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center justify-center transition-colors" type="button" @click="closeDetails">
            <Icon class="text-xl" icon="ph:x-bold" />
          </button>
        </div>
        <div class="p-6 overflow-y-auto flex-grow bg-slate-50/50 dark:bg-slate-950/50">
          <p class="text-slate-500">{{ t("documents.modal.placeholder") }}</p>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { Icon } from "@iconify/vue";
import { getMyDocuments } from "./api/auth";

defineProps<{
  asOfDate: string;
}>();

defineEmits<{
  (e: "new-translation"): void;
  (e: "open-preview"): void;
}>();

const showDetails = ref(false);
const { t } = useI18n();
const modalTitle = ref(t("documents.modal.title"));
const docsLoading = ref(false);
const documents = ref<Array<{ id: string; fileName: string; uploadTime: string; wordCount: number }>>([]);

function formatTimeText(v: string): string {
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return "-";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

async function loadDocuments() {
  docsLoading.value = true;
  try {
    const rows = await getMyDocuments();
    documents.value = (Array.isArray(rows) ? rows : []).map((x) => ({
      id: String(x?.id || "-"),
      fileName: String(x?.file_name || t("profile.untitledDocument")),
      uploadTime: formatTimeText(String(x?.created_at || "")),
      wordCount: Math.max(0, Number(x?.word_count ?? 0)),
    }));
  } catch {
    documents.value = [];
  } finally {
    docsLoading.value = false;
  }
}

function openDetails(name: string) {
  modalTitle.value = t("documents.modal.compareTitle", { name });
  showDetails.value = true;
}

function closeDetails() {
  showDetails.value = false;
}

onMounted(() => {
  void loadDocuments();
});
</script>
