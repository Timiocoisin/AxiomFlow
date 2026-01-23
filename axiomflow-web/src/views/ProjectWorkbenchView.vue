<template>
  <section class="workbench">
    <aside class="workbench-sidebar glass-card">
      <h3>文档结构</h3>
      <div v-if="loading" style="color: #9ca3af">加载中…</div>
      <div v-else-if="error" style="color: #fb7185">{{ error }}</div>
      <div v-else>
        <div style="color: #9ca3af; font-size: 12px; margin-bottom: 10px">
          {{ doc?.document.title }} · {{ doc?.document.lang_in }}→{{ doc?.document.lang_out }}
        </div>
        <div style="display: flex; gap: 10px; margin-bottom: 12px">
          <AppButton primary @click="runTranslate" :disabled="!doc">一键翻译（Ollama）</AppButton>
        </div>
        <div style="display:flex;gap:10px;align-items:center;margin-bottom:12px">
          <input class="simple-input" v-model="search" placeholder="搜索（/ 聚焦，Esc 清空）" style="width:100%" />
        </div>
        <div v-if="jobStatus" style="color: #9ca3af; font-size: 12px; margin-bottom: 12px">
          <div style="display:flex;justify-content:space-between;gap:10px;align-items:center;flex-wrap:wrap">
            <div>任务状态：{{ jobStatus }}</div>
            <div style="display:flex;gap:8px;align-items:center">
              <AppButton v-if="jobDetail?.control === 'running'" @click="pause">暂停</AppButton>
              <AppButton v-else-if="jobDetail?.control === 'paused'" @click="resume">继续</AppButton>
              <AppButton @click="cancel">取消</AppButton>
              <AppButton v-if="jobDetail?.stage === 'failed'" @click="retry">重试</AppButton>
            </div>
          </div>
        </div>
        <div style="max-height: calc(100vh - 220px); overflow: auto; padding-right: 6px">
          <div
            v-for="b in filteredBlocks"
            :key="b.id"
            class="block-item"
            :class="{ active: b.id === activeBlockId }"
            @click="selectBlock(b.id)"
          >
            <div style="font-size: 12px; color: #9ca3af">
              <span v-if="b.type === 'heading'" class="tag-heading">标题</span>
              <span v-else-if="b.type === 'caption'" class="tag-caption">图表说明</span>
              <span v-else-if="b.type === 'formula'" class="tag-formula">公式</span>
              <span v-else-if="b.type === 'figure'" class="tag-figure">图</span>
              <span v-else-if="b.type === 'table'" class="tag-table">表</span>
              #{{ b.reading_order }} · 列 {{ (b.column_index ?? 0) + 1 }}
            </div>
            <div style="font-size: 13px; line-height: 1.5">
              {{ b.text.slice(0, 64) }}{{ b.text.length > 64 ? "…" : "" }}
            </div>
            <div v-if="b.type === 'figure' || b.type === 'table'" style="margin-top: 8px">
              <AppButton @click.stop="openPreview(b.type)">预览{{ b.type === 'figure' ? '图' : '表' }}</AppButton>
            </div>
          </div>
        </div>
      </div>
    </aside>
    <div class="workbench-main glass-card">
      <div class="workbench-columns">
        <div class="pane pane-original">
          <h3 style="display:flex;align-items:center;justify-content:space-between;gap:10px">
            <span>画布校对</span>
            <span v-if="activeBlock" style="color:#9ca3af;font-size:12px">已选：#{{ activeBlock.reading_order }}</span>
          </h3>
          <div v-if="doc" style="height: calc(100% - 34px);">
            <PdfCanvasViewer
              :pdf-url="sourcePdfUrl"
              :page-width="doc.pages[0]?.width || 1000"
              :page-height="doc.pages[0]?.height || 1000"
              :blocks="flatBlocks as any"
              :active-block-id="activeBlockId"
              @select="selectBlock"
              @page="onCanvasPage"
            />
          </div>
          <p v-else class="demo-block" style="color: #9ca3af">加载文档后可在这里进行 bbox 画布校对</p>
        </div>
        <div class="pane pane-translation">
          <h3>译文</h3>
          <div v-if="activeBlock" class="demo-block">
            <div style="margin-bottom: 10px; color: #9ca3af; font-size: 12px">
              {{ activeBlock.translation ? "已生成译文" : "暂无译文（可先点击“一键翻译”）" }}
            </div>
            <label style="display: flex; gap: 8px; align-items: center; margin-bottom: 10px; color: #9ca3af; font-size: 12px">
              <input type="checkbox" v-model="applyAllSameSource" />
              保存时应用到全文同句（提高一致性）
            </label>
            <textarea
              class="simple-input"
              style="width: 100%; min-height: 180px; resize: vertical"
              v-model="editText"
              placeholder="在这里编辑译文…"
            />
            <div style="margin-top: 10px; display: flex; gap: 10px">
              <AppButton primary @click="saveEdit" :disabled="saving">保存</AppButton>
              <AppButton @click="resetEdit" :disabled="saving">重置</AppButton>
            </div>
          </div>
        </div>
      </div>
    </div>
    <aside class="workbench-tools glass-card">
      <h3>工具</h3>
      <div style="display: grid; gap: 10px">
        <div style="color: #9ca3af; font-size: 12px">术语表（项目级）</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px">
          <input class="simple-input" v-model="glossaryTerm" placeholder="术语（英文）" />
          <input class="simple-input" v-model="glossaryTranslation" placeholder="固定译法（中文）" />
        </div>
        <div style="display: flex; gap: 10px; align-items: center">
          <AppButton primary @click="addGlossary" :disabled="!doc">添加/更新术语</AppButton>
          <AppButton @click="refreshGlossary" :disabled="!doc">刷新术语表</AppButton>
        </div>
        <div v-if="Object.keys(glossary).length" style="display: flex; flex-wrap: wrap; gap: 8px">
          <span
            v-for="(v, k) in glossary"
            :key="k"
            class="tag-caption"
            style="cursor: pointer"
            :title="`点击删除：${k} => ${v}`"
            @click="removeGlossary(k)"
          >
            {{ k }} => {{ v }}
          </span>
        </div>
        <div style="color: #9ca3af; font-size: 12px">导出（MVP）</div>
        <AppButton @click="doExport('markdown')" :disabled="!doc">导出 Markdown（内容）</AppButton>
        <AppButton @click="doExport('html')" :disabled="!doc">导出 HTML（内容）</AppButton>
        <AppButton @click="doExport('html-hifi')" :disabled="!doc">导出 HTML（高保真）</AppButton>
        <AppButton @click="doExportDownload('docx')" :disabled="!doc">导出 DOCX</AppButton>
        <AppButton @click="doExportPdf('pdf-mono')" :disabled="!doc">导出 PDF（单语）</AppButton>
        <AppButton @click="doExportPdf('pdf-dual')" :disabled="!doc">导出 PDF（双语）</AppButton>
        <div style="margin-top: 6px; padding: 10px; border-radius: 12px; border: 1px solid rgba(148,163,184,0.15)">
          <div style="color: #9ca3af; font-size: 12px; margin-bottom: 8px">PDF/A（高级）</div>
          <label style="display:flex;gap:8px;align-items:center;color:#9ca3af;font-size:12px;margin-bottom:8px">
            <input type="checkbox" v-model="pdfaEnabled" />
            转换为 PDF/A
          </label>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px">
            <input class="simple-input" v-model="pdfaPart" placeholder="part（1/2/3，可空）" />
            <input class="simple-input" v-model="pdfaConformance" placeholder="conformance（A/B/U，默认B）" />
          </div>
          <label style="display:flex;gap:8px;align-items:center;color:#9ca3af;font-size:12px">
            <input type="checkbox" v-model="subsetFonts" />
            PDF 字体子集化（推荐）
          </label>
        </div>
        <a v-if="pdfUrl" class="nav-link" :href="pdfUrl" target="_blank" rel="noreferrer">
          打开下载链接
        </a>
        <AppButton @click="loadTerms" :disabled="!doc">术语建议（Top 30）</AppButton>
        <div v-if="terms.length" style="display: flex; flex-wrap: wrap; gap: 8px">
          <span
            v-for="t in terms"
            :key="t.term"
            class="tag-heading"
            style="cursor: default"
            :title="`出现次数：${t.count}`"
          >
            {{ t.term }} · {{ t.count }}
          </span>
        </div>
        <textarea
          class="simple-input"
          style="width: 100%; min-height: 180px; resize: vertical"
          v-model="exportText"
          placeholder="导出内容会出现在这里…"
        />
      </div>
    </aside>
  </section>

  <div v-if="previewOpen" class="preview-backdrop" @click="previewOpen = false">
    <div class="preview-modal glass-card" @click.stop>
      <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:10px">
        <div style="font-weight:700">预览{{ previewKind === 'figure' ? '图' : '表' }}</div>
        <AppButton @click="previewOpen = false">关闭</AppButton>
      </div>
      <div v-if="previewLoading" style="color:#9ca3af">生成预览中…</div>
      <div v-else-if="previewImages.length === 0" style="color:#9ca3af">暂无可预览图片（需要先有 regions）。</div>
      <div v-else style="display:grid;grid-template-columns:1fr;gap:10px;max-height:70vh;overflow:auto">
        <img v-for="u in previewImages" :key="u" :src="u" style="width:100%;border-radius:12px;border:1px solid rgba(148,163,184,0.25)" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import AppButton from "@/components/AppButton.vue";
import PdfCanvasViewer from "@/components/PdfCanvasViewer.vue";
import { cancelJob, deleteGlossaryTerm, exportDocument, extractAssets, getDocument, getGlossary, getJob, getSourcePdfUrl, patchBlockTranslation, pauseJob, resumeJob, retryJob, StructuredDoc, suggestTerms, translateDocument, upsertGlossary } from "@/lib/api";

const route = useRoute();
const documentId = computed(() => String(route.params.id || ""));

const doc = ref<StructuredDoc | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

const activeBlockId = ref<string | null>(null);
const editText = ref("");
const saving = ref(false);
const exportText = ref("");
const jobStatus = ref<string | null>(null);
const jobId = ref<string | null>(null);
const jobDetail = ref<any>(null);
const terms = ref<Array<{ term: string; count: number }>>([]);
const pdfUrl = ref<string>("");
const sourcePdfUrl = computed(() => (doc.value ? getSourcePdfUrl(doc.value.document.id) : ""));
const glossary = ref<Record<string, string>>({});
const glossaryTerm = ref("");
const glossaryTranslation = ref("");
const applyAllSameSource = ref(false);
const previewOpen = ref(false);
const previewKind = ref<"figure" | "table">("figure");
const previewLoading = ref(false);
const previewImages = ref<string[]>([]);

// 翻译策略（对齐后端 TranslateStrategy）
const provider = ref<"ollama">("ollama");
const useContext = ref(true);
const contextWindowSize = ref(2);
const useTermConsistency = ref(true);
const useSmartBatching = ref(true);
const search = ref("");

// 导出参数（PDF/A & 字体子集）
const subsetFonts = ref(true);
const pdfaEnabled = ref(false);
const pdfaPart = ref<string>("");
const pdfaConformance = ref<string>("B");

const flatBlocks = computed(() => {
  const blocks: any[] = [];
  for (const p of doc.value?.pages ?? []) blocks.push(...p.blocks);
  return blocks.sort((a, b) => a.reading_order - b.reading_order);
});

const filteredBlocks = computed(() => {
  const q = search.value.trim().toLowerCase();
  if (!q) return flatBlocks.value;
  return flatBlocks.value.filter((b: any) => String(b.text || "").toLowerCase().includes(q) || String(b.translation || "").toLowerCase().includes(q));
});

const activeBlock = computed(() => flatBlocks.value.find((b) => b.id === activeBlockId.value) ?? null);

const selectBlock = (id: string) => {
  activeBlockId.value = id;
  editText.value = activeBlock.value?.translation ?? "";
  persistUiState();
};

const onCanvasPage = (p: number) => {
  // 预留：后续把“当前页”存到 localStorage 做刷新恢复
  lastCanvasPage.value = p;
  persistUiState();
};

const lastCanvasPage = ref<number>(0);

const uiStateKey = computed(() => `axiomflow_workbench_state__${documentId.value}`);

const persistUiState = () => {
  try {
    const payload = {
      activeBlockId: activeBlockId.value,
      lastCanvasPage: lastCanvasPage.value,
      search: search.value,
      jobId: jobId.value,
      strategy: {
        useContext: useContext.value,
        contextWindowSize: contextWindowSize.value,
        useTermConsistency: useTermConsistency.value,
        useSmartBatching: useSmartBatching.value,
      },
      export: {
        subsetFonts: subsetFonts.value,
        pdfaEnabled: pdfaEnabled.value,
        pdfaPart: pdfaPart.value,
        pdfaConformance: pdfaConformance.value,
      },
      ts: Date.now(),
    };
    localStorage.setItem(uiStateKey.value, JSON.stringify(payload));
  } catch {
    // ignore
  }
};

const restoreUiState = () => {
  try {
    const raw = localStorage.getItem(uiStateKey.value);
    if (!raw) return;
    const st = JSON.parse(raw);
    if (st?.search != null) search.value = String(st.search);
    if (st?.activeBlockId) activeBlockId.value = String(st.activeBlockId);
    if (typeof st?.lastCanvasPage === "number") lastCanvasPage.value = st.lastCanvasPage;
    if (st?.jobId) jobId.value = String(st.jobId);
    if (st?.strategy) {
      if (typeof st.strategy.useContext === "boolean") useContext.value = st.strategy.useContext;
      if (typeof st.strategy.contextWindowSize === "number") contextWindowSize.value = st.strategy.contextWindowSize;
      if (typeof st.strategy.useTermConsistency === "boolean") useTermConsistency.value = st.strategy.useTermConsistency;
      if (typeof st.strategy.useSmartBatching === "boolean") useSmartBatching.value = st.strategy.useSmartBatching;
    }
    if (st?.export) {
      if (typeof st.export.subsetFonts === "boolean") subsetFonts.value = st.export.subsetFonts;
      if (typeof st.export.pdfaEnabled === "boolean") pdfaEnabled.value = st.export.pdfaEnabled;
      if (typeof st.export.pdfaPart === "string") pdfaPart.value = st.export.pdfaPart;
      if (typeof st.export.pdfaConformance === "string") pdfaConformance.value = st.export.pdfaConformance;
    }
  } catch {
    // ignore
  }
};

const resetEdit = () => {
  editText.value = activeBlock.value?.translation ?? "";
};

const refresh = async () => {
  loading.value = true;
  error.value = null;
  try {
    doc.value = await getDocument(documentId.value);
    await refreshGlossary();
    restoreUiState();
    if (!activeBlockId.value && doc.value.pages[0]?.blocks[0]?.id) {
      selectBlock(doc.value.pages[0].blocks[0].id);
    } else if (activeBlockId.value) {
      editText.value = activeBlock.value?.translation ?? "";
    }
    // 刷新恢复：如果有未完成的 job，就继续轮询
    if (jobId.value && !jobDetail.value) {
      try {
        jobDetail.value = await getJob(jobId.value);
      } catch {
        // ignore
      }
    }
    if (jobId.value && jobDetail.value && !["success", "failed", "canceled"].includes(String(jobDetail.value.stage))) {
      pollJob(jobId.value);
    }
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    loading.value = false;
  }
};

const runTranslate = async () => {
  if (!doc.value) return;
  const { job_id } = await translateDocument({
    document_id: doc.value.document.id,
    lang_in: doc.value.document.lang_in,
    lang_out: doc.value.document.lang_out,
    provider: provider.value,
    use_context: useContext.value,
    context_window_size: contextWindowSize.value,
    use_term_consistency: useTermConsistency.value,
    use_smart_batching: useSmartBatching.value,
  });
  jobId.value = job_id;
  persistUiState();
  await pollJob(job_id);
  await refresh();
};

const pollJob = async (id: string) => {
  for (let i = 0; i < 240; i++) {
    await new Promise((resolve) => setTimeout(resolve, 800));
    try {
      const j = await getJob(id);
      jobDetail.value = j;
      const pct = Math.round((j?.progress ?? 0) * 100);
      const eta = j?.eta_s != null ? ` · ETA ${Math.round(j.eta_s)}s` : "";
      const done = j?.done != null && j?.total != null ? ` · ${j.done}/${j.total}` : "";
      jobStatus.value = `${j?.stage ?? "unknown"} · ${pct}%${done}${eta}`;
      if (j?.stage === "success" || j?.stage === "failed" || j?.stage === "canceled") break;
    } catch {
      // ignore
    }
  }
};

const pause = async () => {
  if (!jobId.value) return;
  jobDetail.value = await pauseJob(jobId.value);
};

const resume = async () => {
  if (!jobId.value) return;
  jobDetail.value = await resumeJob(jobId.value);
};

const cancel = async () => {
  if (!jobId.value) return;
  jobDetail.value = await cancelJob(jobId.value);
  persistUiState();
};

const retry = async () => {
  if (!jobId.value) return;
  await retryJob(jobId.value);
  await pollJob(jobId.value);
  await refresh();
};

const saveEdit = async () => {
  if (!doc.value || !activeBlock.value) return;
  saving.value = true;
  try {
    await patchBlockTranslation({
      document_id: doc.value.document.id,
      block_id: activeBlock.value.id,
      translation: editText.value,
      apply_all_same_source: applyAllSameSource.value,
    });
    await refresh();
  } finally {
    saving.value = false;
  }
};

const doExport = async (fmt: "markdown" | "html" | "html-hifi") => {
  if (!doc.value) return;
  const res = await exportDocument({ document_id: doc.value.document.id, format: fmt, bilingual: true });
  exportText.value = res.content ?? "";
};

const doExportPdf = async (fmt: "pdf-mono" | "pdf-dual") => {
  if (!doc.value) return;
  const partNum = (() => {
    const s = pdfaPart.value.trim();
    if (!s) return undefined;
    const n = Number(s);
    return n === 1 || n === 2 || n === 3 ? (n as 1 | 2 | 3) : undefined;
  })();
  const conf = (pdfaConformance.value.trim().toUpperCase() || "B") as "A" | "B" | "U";
  const res: any = await exportDocument({
    document_id: doc.value.document.id,
    format: fmt as any,
    bilingual: true,
    subset_fonts: subsetFonts.value,
    convert_to_pdfa: pdfaEnabled.value,
    pdfa_part: partNum,
    pdfa_conformance: conf,
  });
  pdfUrl.value = `http://localhost:8000${res.download_url}`;
  exportText.value = pdfUrl.value;
};

const doExportDownload = async (fmt: "docx" | "pdf" | "pdf-mono" | "pdf-dual") => {
  if (!doc.value) return;
  const partNum = (() => {
    const s = pdfaPart.value.trim();
    if (!s) return undefined;
    const n = Number(s);
    return n === 1 || n === 2 || n === 3 ? (n as 1 | 2 | 3) : undefined;
  })();
  const conf = (pdfaConformance.value.trim().toUpperCase() || "B") as "A" | "B" | "U";
  const res: any = await exportDocument({
    document_id: doc.value.document.id,
    format: fmt as any,
    bilingual: true,
    subset_fonts: subsetFonts.value,
    convert_to_pdfa: pdfaEnabled.value,
    pdfa_part: partNum,
    pdfa_conformance: conf,
  });
  if (res?.download_url) {
    pdfUrl.value = `http://localhost:8000${res.download_url}`;
    exportText.value = pdfUrl.value;
  } else {
    exportText.value = res?.content ?? "";
  }
};

const loadTerms = async () => {
  if (!doc.value) return;
  const res = await suggestTerms({ document_id: doc.value.document.id, top_k: 30 });
  terms.value = res.terms ?? [];
};

const refreshGlossary = async () => {
  if (!doc.value) return;
  const res = await getGlossary({ project_id: doc.value.document.project_id });
  glossary.value = res.glossary ?? {};
};

const addGlossary = async () => {
  if (!doc.value) return;
  const term = glossaryTerm.value.trim();
  const translation = glossaryTranslation.value.trim();
  if (!term || !translation) return;
  await upsertGlossary({ project_id: doc.value.document.project_id, term, translation });
  glossaryTerm.value = "";
  glossaryTranslation.value = "";
  await refreshGlossary();
};

const removeGlossary = async (term: string) => {
  if (!doc.value) return;
  await deleteGlossaryTerm({ project_id: doc.value.document.project_id, term });
  await refreshGlossary();
};

const openPreview = async (kind: "figure" | "table") => {
  if (!doc.value) return;
  previewKind.value = kind;
  previewOpen.value = true;
  previewLoading.value = true;
  previewImages.value = [];
  try {
    const res = await extractAssets({ document_id: doc.value.document.id });
    const urls = (res.assets ?? [])
      .filter((a: any) => a.kind === kind)
      .map((a: any) => `http://localhost:8000${a.download_url}`);
    previewImages.value = urls;
  } finally {
    previewLoading.value = false;
  }
};

onMounted(refresh);
watch(documentId, refresh);

// 快捷键：/ 聚焦搜索；Esc 清空；j/k 或 上下键跳转块
onMounted(() => {
  const handler = (e: KeyboardEvent) => {
    if (e.key === "/" && !e.ctrlKey && !e.metaKey && !e.altKey) {
      e.preventDefault();
      const el = document.querySelector("input.simple-input") as HTMLInputElement | null;
      el?.focus();
      return;
    }
    if (e.key === "Escape") {
      if (search.value) {
        search.value = "";
        persistUiState();
      }
      return;
    }
    const go = (delta: number) => {
      const arr = filteredBlocks.value;
      if (!arr.length) return;
      const idx = arr.findIndex((b: any) => b.id === activeBlockId.value);
      const next = idx < 0 ? 0 : Math.min(arr.length - 1, Math.max(0, idx + delta));
      selectBlock(arr[next].id);
    };
    if (e.key === "j" || e.key === "ArrowDown") go(+1);
    if (e.key === "k" || e.key === "ArrowUp") go(-1);
  };
  window.addEventListener("keydown", handler);
  onUnmounted(() => window.removeEventListener("keydown", handler));
});
</script>


