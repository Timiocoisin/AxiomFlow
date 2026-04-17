<template>
  <div class="min-h-screen flex flex-col bg-slate-100 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
    <nav class="h-16 shrink-0 glass border-b dark:border-slate-800 flex items-center px-4 sm:px-6 z-50">
      <div class="flex items-center gap-4 w-1/3">
        <button class="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors flex items-center gap-2" type="button" @click="$emit('back')">
          <Icon icon="ph:arrow-left-bold" />
          <span class="text-sm font-semibold hidden md:inline">{{ t("preview.backToDocs") }}</span>
        </button>
        <div class="h-6 w-px bg-slate-200 dark:bg-slate-800 hidden md:block"></div>
        <div class="truncate max-w-[220px]">
          <h1 class="text-sm font-bold truncate">{{ documentName || "-" }}</h1>
          <p class="text-[10px] text-slate-500 uppercase font-mono tracking-tighter">{{ pageCount }} Pages</p>
        </div>
      </div>
      <div class="flex-grow flex justify-center gap-2">
        <div class="flex items-center bg-white dark:bg-slate-900 rounded-lg border dark:border-slate-800 p-1 shadow-sm">
          <button class="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md transition-colors" type="button" @click="changeZoom(-0.25)"><Icon icon="ph:minus-bold" /></button>
          <span class="text-xs font-bold w-12 text-center">{{ Math.round(currentZoom * 100) }}%</span>
          <button class="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md transition-colors" type="button" @click="changeZoom(0.25)"><Icon icon="ph:plus-bold" /></button>
        </div>
        <div class="flex items-center bg-white dark:bg-slate-900 rounded-lg border dark:border-slate-800 p-1 shadow-sm">
          <button class="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md transition-colors disabled:opacity-40" type="button" :disabled="currentPage <= 1" @click="goPrevPage"><Icon icon="ph:caret-left-bold" /></button>
          <input class="w-8 text-center text-xs font-bold bg-transparent outline-none" type="text" :value="currentPage" readonly />
          <span class="text-xs text-slate-400">/ {{ pageCount }}</span>
          <button class="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md transition-colors disabled:opacity-40" type="button" :disabled="currentPage >= pageCount" @click="goNextPage"><Icon icon="ph:caret-right-bold" /></button>
        </div>
      </div>
      <div class="flex items-center justify-end gap-3 w-1/3">
        <button class="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors" type="button" @click="$emit('toggle-theme')">
          <Icon class="text-lg block dark:hidden" icon="ph:moon-bold" />
          <Icon class="text-lg hidden dark:block text-yellow-400" icon="ph:sun-bold" />
        </button>
        <button class="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-700 transition-all flex items-center gap-2 shadow-lg shadow-indigo-200 dark:shadow-none" type="button">
          <Icon icon="ph:download-simple-bold" />
          <span class="hidden sm:inline">{{ t("preview.export") }}</span>
        </button>
      </div>
    </nav>

    <div class="h-12 bg-white dark:bg-slate-900 border-b dark:border-slate-800 flex items-center justify-between px-6 z-40">
      <div class="flex items-center gap-6">
        <div class="flex items-center gap-2">
          <button class="relative inline-flex h-5 w-9 items-center rounded-full transition-colors" :class="isSync ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-slate-700'" type="button" @click="isSync = !isSync">
            <span class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform" :class="isSync ? 'translate-x-4' : 'translate-x-0.5'"></span>
          </button>
          <span class="text-xs font-medium text-slate-500">{{ t("preview.syncScroll") }}</span>
        </div>
      </div>
      <div class="flex items-center gap-4 text-xs font-medium text-slate-500">
        <div class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>{{ t("preview.realtimeSynced") }}</div>
        <span>{{ serviceTime }}</span>
      </div>
    </div>

    <div class="flex-grow flex overflow-hidden">
      <div ref="originalPaneRef" class="pdf-viewport border-r dark:border-slate-800 bg-slate-200/50 dark:bg-slate-900/30 basis-1/2" @scroll="onOriginalScroll">
        <div class="p-0 sm:p-1">
          <div v-if="pdfPages.length > 0" class="space-y-6">
            <div
              v-for="(pageNo, idx) in pdfPages"
              :key="`src-p-${pageNo}`"
              :ref="(el) => setPageWrapRef(el, idx)"
              class="pdf-page p-0 sm:p-1"
              :style="{ transform: `scale(${currentZoom})` }"
            >
              <div class="bg-white dark:bg-slate-900 overflow-hidden border-y border-slate-200 dark:border-slate-700 shadow-sm">
                <canvas :ref="(el) => setPageCanvasRef(el, idx)" class="block w-full h-auto"></canvas>
              </div>
            </div>
          </div>
          <div v-else class="pdf-page p-0 sm:p-1">
            <div class="h-40 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 flex items-center justify-center text-sm text-slate-500">
              {{ t("documents.loading") }}
            </div>
          </div>
        </div>
      </div>

      <div ref="translatedPaneRef" class="pdf-viewport bg-white/50 dark:bg-slate-900/10 basis-1/2" @scroll="onTranslatedScroll">
        <div class="p-0 sm:p-1">
          <div v-if="pdfPages.length > 0" class="space-y-6">
            <div v-for="pageNo in pdfPages" :key="`t-${pageNo}`" class="pdf-page p-0 sm:p-1" :style="{ transform: `scale(${currentZoom})` }">
              <div class="bg-white dark:bg-slate-900 overflow-hidden border-y border-slate-200 dark:border-slate-700 shadow-sm p-8 sm:p-10 space-y-5">
              <div class="text-sm font-semibold text-slate-700 dark:text-slate-200">{{ t("preview.translatedLabel") }} · Page {{ pageNo }}</div>
              <div class="h-4 bg-slate-100 dark:bg-slate-800/70 w-full rounded"></div>
              <div class="h-4 bg-slate-100 dark:bg-slate-800/70 w-[92%] rounded"></div>
              <div class="h-4 bg-slate-100 dark:bg-slate-800/70 w-[96%] rounded"></div>
              <div class="h-4 bg-slate-100 dark:bg-slate-800/70 w-[90%] rounded"></div>
              <div class="h-4 bg-slate-100 dark:bg-slate-800/70 w-[94%] rounded"></div>
              <div class="h-4 bg-slate-100 dark:bg-slate-800/70 w-[88%] rounded"></div>
              <div class="h-4 bg-slate-100 dark:bg-slate-800/70 w-[95%] rounded"></div>
              <div class="h-4 bg-slate-100 dark:bg-slate-800/70 w-[91%] rounded"></div>
              </div>
            </div>
          </div>
          <div v-else class="pdf-page p-0 sm:p-1">
            <div class="h-40 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 flex items-center justify-center text-sm text-slate-500">
              {{ t("documents.loading") }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showOverlay" class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[100] flex items-center justify-center">
      <div class="bg-white dark:bg-slate-900 rounded-3xl p-8 max-w-sm w-full text-center shadow-2xl border dark:border-slate-800">
        <div class="space-y-6">
          <div class="relative w-24 h-24 mx-auto">
            <div class="absolute inset-0 border-4 border-indigo-100 dark:border-indigo-900/30 rounded-full"></div>
            <div class="absolute inset-0 border-4 border-indigo-600 rounded-full border-t-transparent animate-spin"></div>
            <div class="absolute inset-0 flex items-center justify-center"><Icon class="text-3xl text-indigo-600" icon="ph:translate-bold" /></div>
          </div>
          <div>
            <h3 class="text-xl font-bold mb-2">{{ t("preview.generatingTitle") }}</h3>
            <p class="text-sm text-slate-500">{{ t("preview.generatingDesc") }}</p>
          </div>
          <div class="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden"><div class="bg-indigo-600 h-full w-[65%]"></div></div>
          <div class="text-xs font-mono text-slate-400">Progress: 65% (Page 9/14)</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { Icon } from "@iconify/vue";
import { GlobalWorkerOptions, getDocument } from "pdfjs-dist";
import pdfWorkerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import { downloadMyDocument } from "./api/auth";

const props = defineProps<{ serviceTime: string; documentId: string; documentName: string; documentMimeType: string }>();
defineEmits<{ (e: "back"): void; (e: "toggle-theme"): void }>();

const isSync = ref(true);
const currentZoom = ref(1);
const showOverlay = ref(true);
const originalPaneRef = ref<HTMLElement | null>(null);
const translatedPaneRef = ref<HTMLElement | null>(null);
const { t } = useI18n();
const sourcePdfUrl = ref("");
const pdfPages = ref<number[]>([]);
const pageCanvasRefs = ref<Array<HTMLCanvasElement | null>>([]);
const pageWrapRefs = ref<Array<HTMLElement | null>>([]);
const pageCount = ref(1);
const currentPage = ref(1);
let renderVersion = 0;

GlobalWorkerOptions.workerSrc = pdfWorkerUrl;

function changeZoom(delta: number) {
  currentZoom.value = Math.min(Math.max(0.25, currentZoom.value + delta), 4);
}
function setPageCanvasRef(el: Element | null, idx: number) {
  pageCanvasRefs.value[idx] = (el as HTMLCanvasElement | null) || null;
}
function setPageWrapRef(el: Element | null, idx: number) {
  pageWrapRefs.value[idx] = (el as HTMLElement | null) || null;
}
function scrollToPage(pageNum: number) {
  const pane = originalPaneRef.value;
  const wrap = pageWrapRefs.value[pageNum - 1];
  if (!pane || !wrap) return;
  pane.scrollTo({ top: Math.max(0, wrap.offsetTop - 12), behavior: "smooth" });
}
function goPrevPage() {
  const next = Math.max(1, currentPage.value - 1);
  currentPage.value = next;
  scrollToPage(next);
}
function goNextPage() {
  const next = Math.min(pageCount.value, currentPage.value + 1);
  currentPage.value = next;
  scrollToPage(next);
}
function onOriginalScroll() {
  const pane = originalPaneRef.value;
  if (!pane) return;
  if (isSync.value && translatedPaneRef.value) {
    translatedPaneRef.value.scrollTop = pane.scrollTop;
  }
  const anchor = pane.scrollTop + 24;
  for (let i = 0; i < pageWrapRefs.value.length; i += 1) {
    const wrap = pageWrapRefs.value[i];
    if (!wrap) continue;
    if (anchor >= wrap.offsetTop) {
      currentPage.value = i + 1;
    } else {
      break;
    }
  }
}
function onTranslatedScroll() {
  if (!isSync.value || !originalPaneRef.value || !translatedPaneRef.value) return;
  originalPaneRef.value.scrollTop = translatedPaneRef.value.scrollTop;
}

async function loadSourcePdf() {
  const currentRun = ++renderVersion;
  if (!props.documentId) return;
  if (sourcePdfUrl.value) {
    URL.revokeObjectURL(sourcePdfUrl.value);
    sourcePdfUrl.value = "";
  }
  pdfPages.value = [];
  pageCanvasRefs.value = [];
  pageWrapRefs.value = [];
  pageCount.value = 1;
  currentPage.value = 1;
  try {
    const { blob } = await downloadMyDocument(props.documentId, "original");
    if (currentRun !== renderVersion) return;
    sourcePdfUrl.value = URL.createObjectURL(blob);
    const isPdf = String(props.documentMimeType || "").toLowerCase().includes("pdf") || (props.documentName || "").toLowerCase().endsWith(".pdf");
    if (isPdf) {
      const bytes = await blob.arrayBuffer();
      if (currentRun !== renderVersion) return;
      const loadingTask = getDocument({ data: bytes });
      const pdf = await loadingTask.promise;
      if (currentRun !== renderVersion) return;
      pageCount.value = Math.max(1, pdf.numPages);
      pdfPages.value = Array.from({ length: pageCount.value }, (_, i) => i + 1);
      await nextTick();
      for (let i = 0; i < pageCount.value; i += 1) {
        if (currentRun !== renderVersion) return;
        const page = await pdf.getPage(i + 1);
        const viewport = page.getViewport({ scale: 1.75 });
        const canvas = pageCanvasRefs.value[i];
        if (!canvas) continue;
        const ctx = canvas.getContext("2d");
        if (!ctx) continue;
        canvas.width = Math.floor(viewport.width);
        canvas.height = Math.floor(viewport.height);
        await page.render({ canvasContext: ctx, viewport }).promise;
      }
      await loadingTask.destroy();
    } else {
      pageCount.value = 1;
      pdfPages.value = [];
    }
  } catch {
    pageCount.value = 1;
    pdfPages.value = [];
  }
}

onMounted(() => {
  window.setTimeout(() => (showOverlay.value = false), 1800);
  void loadSourcePdf();
});

onBeforeUnmount(() => {
  if (sourcePdfUrl.value) URL.revokeObjectURL(sourcePdfUrl.value);
});

watch(
  () => props.documentId,
  () => {
    void loadSourcePdf();
  },
);
</script>

<style scoped>
.pdf-viewport {
  height: calc(100vh - 112px);
  overflow-y: auto;
  scrollbar-width: thin;
}

.pdf-page {
  background: white;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  margin: 0 auto;
  min-height: calc(100vh - 180px);
  width: 100%;
  max-width: none;
  transform-origin: top center;
  transition: transform 0.2s ease;
}

:global(body.theme-dark) .pdf-page {
  background: #1e293b;
  border: 1px solid #334155;
}

</style>
