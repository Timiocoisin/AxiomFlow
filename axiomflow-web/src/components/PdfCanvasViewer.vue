<template>
  <div class="pdf-viewer">
    <div class="pdf-toolbar" style="display:flex;gap:10px;align-items:center;justify-content:space-between;margin-bottom:10px">
      <div style="display:flex;gap:8px;align-items:center">
        <AppButton @click="prevPage" :disabled="pageIndex <= 0">上一页</AppButton>
        <AppButton @click="nextPage" :disabled="pageIndex >= numPages - 1">下一页</AppButton>
        <div style="color:#9ca3af;font-size:12px">第 {{ pageIndex + 1 }} / {{ numPages }} 页</div>
      </div>
      <div style="display:flex;gap:10px;align-items:center">
        <label style="display:flex;gap:8px;align-items:center;color:#9ca3af;font-size:12px">
          <input type="checkbox" v-model="onlyIssues" />
          只看异常
        </label>
        <select class="simple-input" v-model="filterType" style="padding:8px 10px">
          <option value="">全部类型</option>
          <option value="heading">标题</option>
          <option value="paragraph">正文</option>
          <option value="caption">图表说明</option>
          <option value="formula">公式</option>
          <option value="figure">图</option>
          <option value="table">表</option>
        </select>
        <label style="display:flex;gap:8px;align-items:center;color:#9ca3af;font-size:12px">
          <input type="checkbox" v-model="bilingual" />
          双语叠加
        </label>
      </div>
    </div>

    <div ref="scrollEl" class="pdf-scroll">
      <div class="pdf-page" :style="{ width: `${viewportW}px` }">
        <div class="canvas-wrap" :style="{ width: `${viewportW}px`, height: `${viewportH}px` }">
          <canvas ref="canvasEl" :width="viewportW" :height="viewportH" />
          <div class="overlay" :style="{ width: `${viewportW}px`, height: `${viewportH}px` }">
            <div
              v-for="b in visibleBlocks"
              :key="b.id"
              class="bbox"
              :class="[colorClass(b.type), { active: b.id === activeBlockId }]"
              :style="bboxStyle(b)"
              @click.stop="onClickBlock(b.id)"
              :title="tooltipText(b)"
            >
              <div v-if="bilingual" class="bbox-text">
                <div class="bbox-text-src">{{ trimText(b.text) }}</div>
                <div class="bbox-text-tr">{{ trimText(b.translation || '') }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import AppButton from "@/components/AppButton.vue";
import * as pdfjsLib from "pdfjs-dist";
// @ts-ignore
import pdfWorker from "pdfjs-dist/build/pdf.worker?url";

type Block = {
  id: string;
  type: string;
  text: string;
  translation: string | null;
  bbox: { page: number; x0: number; y0: number; x1: number; y1: number };
  translation_failed?: boolean;
  translation_error?: string;
};

const props = defineProps<{
  pdfUrl: string;
  pageWidth: number;
  pageHeight: number;
  blocks: Block[];
  activeBlockId: string | null;
  initialPageIndex?: number;
}>();

const emit = defineEmits<{
  (e: "select", id: string): void;
  (e: "page", pageIndex: number): void;
}>();

const canvasEl = ref<HTMLCanvasElement | null>(null);
const scrollEl = ref<HTMLDivElement | null>(null);
const pdfDoc = ref<any>(null);
const pageIndex = ref<number>(props.initialPageIndex ?? 0);
const numPages = ref<number>(1);

const onlyIssues = ref(false);
const filterType = ref<string>("");
const bilingual = ref(false);

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker as any;

const scale = computed(() => {
  // 让页面宽度适配容器（最小 0.6，最大 1.6）
  const cw = scrollEl.value?.clientWidth ? scrollEl.value.clientWidth - 6 : 900;
  const s = cw / Math.max(1, props.pageWidth);
  return Math.min(1.6, Math.max(0.6, s));
});

const viewportW = computed(() => Math.round(props.pageWidth * scale.value));
const viewportH = computed(() => Math.round(props.pageHeight * scale.value));

const blocksOnPage = computed(() => props.blocks.filter((b) => (b.bbox?.page ?? 0) === pageIndex.value));

const visibleBlocks = computed(() => {
  let bs = blocksOnPage.value;
  if (filterType.value) bs = bs.filter((b) => b.type === filterType.value);
  if (onlyIssues.value) bs = bs.filter((b) => !!b.translation_failed || (b.translation || "").startsWith("[翻译失败"));
  return bs;
});

const bboxStyle = (b: Block) => {
  const x = b.bbox.x0 * scale.value;
  const y = b.bbox.y0 * scale.value;
  const w = (b.bbox.x1 - b.bbox.x0) * scale.value;
  const h = (b.bbox.y1 - b.bbox.y0) * scale.value;
  return {
    left: `${x}px`,
    top: `${y}px`,
    width: `${Math.max(1, w)}px`,
    height: `${Math.max(1, h)}px`,
  } as any;
};

const colorClass = (t: string) => {
  if (t === "heading") return "c-heading";
  if (t === "caption") return "c-caption";
  if (t === "formula") return "c-formula";
  if (t === "figure") return "c-figure";
  if (t === "table") return "c-table";
  return "c-paragraph";
};

const trimText = (s: string) => {
  const v = (s || "").trim().replace(/\s+/g, " ");
  return v.length > 80 ? v.slice(0, 80) + "…" : v;
};

const tooltipText = (b: Block) => {
  const p = `p${(b.bbox?.page ?? 0) + 1}`;
  const t = b.type || "block";
  const err = b.translation_failed ? `\nERROR: ${b.translation_error || ""}` : "";
  return `${p} · ${t}\n${trimText(b.text)}${err}`;
};

const renderPage = async () => {
  if (!canvasEl.value || !pdfDoc.value) return;
  try {
    const page = await pdfDoc.value.getPage(pageIndex.value + 1);
    const vp = page.getViewport({ scale: scale.value });
    const canvas = canvasEl.value;
    canvas.width = Math.round(vp.width);
    canvas.height = Math.round(vp.height);
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    await page.render({ canvasContext: ctx, viewport: vp }).promise;
    emit("page", pageIndex.value);
  } catch (err) {
    console.error("[PdfCanvasViewer] renderPage error", err);
  }
};

const ensureLoaded = async () => {
  if (pdfDoc.value) return;
  const loadingTask = pdfjsLib.getDocument({ url: props.pdfUrl, withCredentials: false });
  pdfDoc.value = await loadingTask.promise;
  numPages.value = pdfDoc.value.numPages || 1;
};

const prevPage = async () => {
  pageIndex.value = Math.max(0, pageIndex.value - 1);
  await renderPage();
};

const nextPage = async () => {
  pageIndex.value = Math.min(numPages.value - 1, pageIndex.value + 1);
  await renderPage();
};

const onClickBlock = (id: string) => {
  emit("select", id);
};

// 当外部选中块时，自动跳到对应页并滚动到位置
watch(
  () => props.activeBlockId,
  async (id) => {
    if (!id) return;
    const b = props.blocks.find((x) => x.id === id);
    if (!b) return;
    if (b.bbox.page !== pageIndex.value) {
      pageIndex.value = b.bbox.page;
      await renderPage();
    }
    // 尝试滚动到 bbox 附近
    const y = b.bbox.y0 * scale.value;
    scrollEl.value?.scrollTo({ top: Math.max(0, y - 120), behavior: "smooth" });
  }
);

watch(scale, async () => {
  // 容器宽度变化时重绘
  await renderPage();
});

onMounted(async () => {
  await ensureLoaded();
  await renderPage();
});
</script>

<style scoped>
.pdf-viewer {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.pdf-scroll {
  flex: 1;
  overflow: auto;
  padding: 4px 2px;
}

.canvas-wrap {
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.25);
  background: rgba(2, 6, 23, 0.2);
}

canvas {
  display: block;
}

.overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.bbox {
  position: absolute;
  border: 1px solid rgba(56, 189, 248, 0.75);
  background: rgba(56, 189, 248, 0.08);
  border-radius: 6px;
  pointer-events: auto;
  cursor: pointer;
  transition: box-shadow 0.12s ease-out, transform 0.12s ease-out, border-color 0.12s ease-out;
}

.bbox:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 28px rgba(56, 189, 248, 0.22);
}

.bbox.active {
  border-color: rgba(110, 231, 183, 0.9);
  box-shadow: 0 12px 32px rgba(110, 231, 183, 0.22);
}

.bbox-text {
  position: absolute;
  left: 6px;
  top: 6px;
  right: 6px;
  bottom: 6px;
  overflow: hidden;
  color: #e5e7eb;
  font-size: 10px;
  line-height: 1.35;
  text-shadow: 0 2px 8px rgba(2, 6, 23, 0.8);
}

.bbox-text-src {
  color: rgba(191, 219, 254, 1);
  margin-bottom: 4px;
}

.bbox-text-tr {
  color: rgba(110, 231, 183, 1);
}

.c-heading {
  border-color: rgba(147, 197, 253, 0.95);
  background: rgba(59, 130, 246, 0.10);
}
.c-paragraph {
  border-color: rgba(148, 163, 184, 0.7);
  background: rgba(148, 163, 184, 0.06);
}
.c-caption {
  border-color: rgba(110, 231, 183, 0.9);
  background: rgba(16, 185, 129, 0.10);
}
.c-formula {
  border-color: rgba(216, 180, 254, 0.95);
  background: rgba(168, 85, 247, 0.10);
}
.c-figure {
  border-color: rgba(253, 230, 138, 0.95);
  background: rgba(245, 158, 11, 0.10);
}
.c-table {
  border-color: rgba(186, 230, 253, 0.95);
  background: rgba(14, 165, 233, 0.10);
}
</style>


