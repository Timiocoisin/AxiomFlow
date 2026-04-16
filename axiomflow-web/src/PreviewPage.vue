<template>
  <div class="min-h-screen flex flex-col bg-slate-100 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
    <nav class="h-16 shrink-0 glass border-b dark:border-slate-800 flex items-center px-4 sm:px-6 z-50">
      <div class="flex items-center gap-4 w-1/3">
        <button class="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors flex items-center gap-2" type="button" @click="$emit('back')">
          <Icon icon="ph:arrow-left-bold" />
          <span class="text-sm font-semibold hidden md:inline">返回文档</span>
        </button>
        <div class="h-6 w-px bg-slate-200 dark:bg-slate-800 hidden md:block"></div>
        <div class="truncate max-w-[220px]">
          <h1 class="text-sm font-bold truncate">2026年Q1季度财报分析报告.pdf</h1>
          <p class="text-[10px] text-slate-500 uppercase font-mono tracking-tighter">14 Pages • 2.4MB • Translated</p>
        </div>
      </div>
      <div class="flex-grow flex justify-center gap-2">
        <div class="flex items-center bg-white dark:bg-slate-900 rounded-lg border dark:border-slate-800 p-1 shadow-sm">
          <button class="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md transition-colors" type="button" @click="changeZoom(-0.25)"><Icon icon="ph:minus-bold" /></button>
          <span class="text-xs font-bold w-12 text-center">{{ Math.round(currentZoom * 100) }}%</span>
          <button class="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md transition-colors" type="button" @click="changeZoom(0.25)"><Icon icon="ph:plus-bold" /></button>
        </div>
        <div class="flex items-center bg-white dark:bg-slate-900 rounded-lg border dark:border-slate-800 p-1 shadow-sm">
          <button class="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md transition-colors" type="button"><Icon icon="ph:caret-left-bold" /></button>
          <input class="w-8 text-center text-xs font-bold bg-transparent outline-none" type="text" value="1" />
          <span class="text-xs text-slate-400">/ 14</span>
          <button class="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md transition-colors" type="button"><Icon icon="ph:caret-right-bold" /></button>
        </div>
      </div>
      <div class="flex items-center justify-end gap-3 w-1/3">
        <button class="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors" type="button" @click="$emit('toggle-theme')">
          <Icon class="text-lg block dark:hidden" icon="ph:moon-bold" />
          <Icon class="text-lg hidden dark:block text-yellow-400" icon="ph:sun-bold" />
        </button>
        <button class="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-700 transition-all flex items-center gap-2 shadow-lg shadow-indigo-200 dark:shadow-none" type="button">
          <Icon icon="ph:download-simple-bold" />
          <span class="hidden sm:inline">导出</span>
        </button>
      </div>
    </nav>

    <div class="h-12 bg-white dark:bg-slate-900 border-b dark:border-slate-800 flex items-center justify-between px-6 z-40">
      <div class="flex items-center gap-6">
        <div class="flex items-center gap-2">
          <button class="relative inline-flex h-5 w-9 items-center rounded-full transition-colors" :class="isSync ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-slate-700'" type="button" @click="isSync = !isSync">
            <span class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform" :class="isSync ? 'translate-x-4' : 'translate-x-0.5'"></span>
          </button>
          <span class="text-xs font-medium text-slate-500">同步滚动</span>
        </div>
        <div class="h-4 w-px bg-slate-200 dark:bg-slate-800"></div>
        <div class="flex items-center gap-1">
          <button class="p-1.5 rounded" :class="compareMode === 'side' ? 'bg-indigo-50 dark:bg-indigo-900/40 text-indigo-600' : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500'" type="button" @click="compareMode = 'side'"><Icon icon="ph:layout-bold" /></button>
          <button class="p-1.5 rounded" :class="compareMode === 'vertical' ? 'bg-indigo-50 dark:bg-indigo-900/40 text-indigo-600' : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500'" type="button" @click="compareMode = 'vertical'"><Icon class="rotate-90" icon="ph:columns-bold" /></button>
        </div>
      </div>
      <div class="flex items-center gap-4 text-xs font-medium text-slate-500">
        <div class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>翻译已实时同步</div>
        <span>{{ serviceTime }}</span>
      </div>
    </div>

    <div class="flex-grow flex overflow-hidden" :class="compareMode === 'vertical' ? 'flex-col' : ''">
      <div ref="originalPaneRef" class="pdf-viewport border-r dark:border-slate-800 bg-slate-200/50 dark:bg-slate-900/30" :class="compareMode === 'vertical' ? 'basis-1/2 border-r-0 border-b' : ''" :style="compareMode === 'side' ? { flex: `0 0 ${leftPanePercent}%` } : undefined" @scroll="onOriginalScroll">
        <div class="p-8">
          <div class="flex justify-between items-center mb-4 sticky top-0 bg-slate-200/80 dark:bg-slate-900/80 backdrop-blur-sm py-2 px-4 rounded-lg z-10 border dark:border-slate-800">
            <span class="text-xs font-bold uppercase tracking-widest text-slate-400">原文 (EN)</span>
            <Icon class="text-slate-400" icon="ph:globe-bold" />
          </div>
          <div v-for="i in 2" :key="`o-${i}`" class="pdf-page p-12 space-y-4" :style="{ transform: `scale(${currentZoom})` }">
            <div class="h-8 bg-slate-200 dark:bg-slate-700 w-3/4 rounded"></div>
            <div class="h-4 bg-slate-100 dark:bg-slate-800 w-full rounded"></div>
            <div class="h-4 bg-slate-100 dark:bg-slate-800 w-full rounded"></div>
            <div class="h-64 bg-slate-100 dark:bg-slate-800 w-full rounded-xl my-8"></div>
          </div>
        </div>
      </div>

      <div v-if="compareMode === 'side'" id="resizer" @mousedown="startResize"></div>

      <div ref="translatedPaneRef" class="pdf-viewport bg-white/50 dark:bg-slate-900/10 flex-1" :class="compareMode === 'vertical' ? 'basis-1/2' : ''" @scroll="onTranslatedScroll">
        <div class="p-8">
          <div class="flex justify-between items-center mb-4 sticky top-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm py-2 px-4 rounded-lg z-10 border dark:border-slate-800">
            <span class="text-xs font-bold uppercase tracking-widest text-indigo-600">译文 (ZH)</span>
            <Icon class="text-green-500" icon="ph:check-circle-fill" />
          </div>
          <div v-for="i in 2" :key="`t-${i}`" class="pdf-page p-12 space-y-4" :style="{ transform: `scale(${currentZoom})` }">
            <div class="h-8 bg-indigo-50 dark:bg-indigo-900/20 w-3/4 rounded border-l-4 border-indigo-500 pl-4 flex items-center font-bold text-slate-800 dark:text-slate-200">2026年Q1季度财报分析报告</div>
            <div class="h-4 bg-slate-50 dark:bg-slate-800/50 w-full rounded"></div>
            <div class="h-4 bg-slate-50 dark:bg-slate-800/50 w-full rounded"></div>
            <div class="h-64 bg-slate-50 dark:bg-slate-800/50 w-full rounded-xl my-8"></div>
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
            <h3 class="text-xl font-bold mb-2">正在生成译文...</h3>
            <p class="text-sm text-slate-500">我们的 AI 正在处理复杂布局和术语，请稍候。</p>
          </div>
          <div class="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden"><div class="bg-indigo-600 h-full w-[65%]"></div></div>
          <div class="text-xs font-mono text-slate-400">Progress: 65% (Page 9/14)</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { Icon } from "@iconify/vue";

defineProps<{ serviceTime: string }>();
defineEmits<{ (e: "back"): void; (e: "toggle-theme"): void }>();

const isSync = ref(true);
const currentZoom = ref(1);
const compareMode = ref<"side" | "vertical">("side");
const showOverlay = ref(true);
const leftPanePercent = ref(50);
const resizing = ref(false);
const originalPaneRef = ref<HTMLElement | null>(null);
const translatedPaneRef = ref<HTMLElement | null>(null);

function changeZoom(delta: number) {
  currentZoom.value = Math.min(Math.max(0.25, currentZoom.value + delta), 4);
}
function onOriginalScroll() {
  if (!isSync.value || !originalPaneRef.value || !translatedPaneRef.value) return;
  translatedPaneRef.value.scrollTop = originalPaneRef.value.scrollTop;
}
function onTranslatedScroll() {
  if (!isSync.value || !originalPaneRef.value || !translatedPaneRef.value) return;
  originalPaneRef.value.scrollTop = translatedPaneRef.value.scrollTop;
}
function startResize() {
  resizing.value = true;
  document.body.style.cursor = "col-resize";
}
function onMouseMove(e: MouseEvent) {
  if (!resizing.value || compareMode.value !== "side") return;
  const percentage = (e.clientX / window.innerWidth) * 100;
  if (percentage > 20 && percentage < 80) leftPanePercent.value = percentage;
}
function stopResize() {
  if (!resizing.value) return;
  resizing.value = false;
  document.body.style.cursor = "";
}

onMounted(() => {
  window.setTimeout(() => (showOverlay.value = false), 1800);
  document.addEventListener("mousemove", onMouseMove);
  document.addEventListener("mouseup", stopResize);
});

onBeforeUnmount(() => {
  document.removeEventListener("mousemove", onMouseMove);
  document.removeEventListener("mouseup", stopResize);
});
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
  margin: 20px auto;
  min-height: 520px;
  width: 100%;
  max-width: 600px;
  transform-origin: top center;
  transition: transform 0.2s ease;
}

:global(body.theme-dark) .pdf-page {
  background: #1e293b;
  border: 1px solid #334155;
}

#resizer {
  cursor: col-resize;
  width: 4px;
  background: transparent;
  transition: background 0.2s;
}
#resizer:hover {
  background: #6366f1;
}
</style>
