<template>
  <section class="workbench">
    <div class="workbench-main glass-card">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px">
        <div style="display:flex;align-items:center;gap:10px">
          <AppButton @click="goBackToDashboard">返回文档列表</AppButton>
          <div style="color:#9ca3af;font-size:12px">
            {{ doc?.document.title }} · {{ doc?.document.lang_in }}→{{ doc?.document.lang_out }}
          </div>
        </div>
        <div style="display:flex;gap:10px;align-items:center">
          <AppButton primary @click="runTranslateAndExport" :disabled="!doc || translating">
            {{ translating ? "翻译中…" : "一键翻译并生成译文 PDF" }}
          </AppButton>
          <div v-if="jobStatus" style="color:#9ca3af;font-size:12px">
            {{ jobStatus }}
          </div>
        </div>
      </div>

      <div class="workbench-columns">
        <div class="pane pane-original">
          <h3>原文 PDF</h3>
          <div v-if="doc" style="height: calc(100% - 30px);">
            <PdfCanvasViewer
              :pdf-url="sourcePdfUrl"
              :page-width="doc.pages[0]?.width || 1000"
              :page-height="doc.pages[0]?.height || 1000"
              :blocks="[] as any"
              :active-block-id="null"
              :continuous="true"
            />
          </div>
          <p v-else class="demo-block" style="color: #9ca3af">加载文档后将显示原文 PDF</p>
        </div>

        <div class="pane pane-translation">
          <h3>译文 PDF</h3>
          <div v-if="translatedPdfUrl" style="height: calc(100% - 30px);">
            <PdfCanvasViewer
              :pdf-url="translatedPdfUrl"
              :page-width="doc?.pages[0]?.width || 1000"
              :page-height="doc?.pages[0]?.height || 1000"
              :blocks="[] as any"
              :active-block-id="null"
              :continuous="true"
            />
          </div>
          <div v-else class="demo-block" style="color:#9ca3af">
            暂无译文 PDF，请先点击右上角「一键翻译并生成译文 PDF」，原文会先加载，译文生成后会自动显示在此处。
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import AppButton from "@/components/AppButton.vue";
import PdfCanvasViewer from "@/components/PdfCanvasViewer.vue";
import { exportDocument, getDocument, getJob, getSourcePdfUrl, StructuredDoc, translateDocument } from "@/lib/api";

const route = useRoute();
const router = useRouter();
const documentId = computed(() => String(route.params.id || ""));

const doc = ref<StructuredDoc | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

const jobStatus = ref<string | null>(null);
const jobId = ref<string | null>(null);
const translating = ref(false);

const pdfUrl = ref<string>("");
const translatedPdfUrl = computed(() => pdfUrl.value || "");
const sourcePdfUrl = computed(() => (doc.value ? getSourcePdfUrl(doc.value.document.id) : ""));

const pollJob = async (id: string) => {
  for (let i = 0; i < 240; i++) {
    await new Promise((resolve) => setTimeout(resolve, 800));
    try {
      const j = await getJob(id);
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
const refresh = async () => {
  loading.value = true;
  error.value = null;
  try {
    doc.value = await getDocument(documentId.value);
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    loading.value = false;
  }
};

const runTranslateAndExport = async () => {
  if (!doc.value || translating.value) return;
  translating.value = true;
  try {
    const { job_id } = await translateDocument({
      document_id: doc.value.document.id,
      lang_in: doc.value.document.lang_in,
      lang_out: doc.value.document.lang_out,
    });
    jobId.value = job_id;
    await pollJob(job_id);
    const res: any = await exportDocument({
      document_id: doc.value.document.id,
      format: "pdf-dual" as any,
      bilingual: true,
      subset_fonts: true,
      convert_to_pdfa: false,
    });
    if (res?.download_url) {
      pdfUrl.value = `http://localhost:8000${res.download_url}`;
    }
  } finally {
    translating.value = false;
  }
};

const goBackToDashboard = () => {
  router.push({ name: "dashboard" });
};

onMounted(refresh);
watch(documentId, refresh);
</script>

<style scoped>
.workbench {
  display: flex;
  height: calc(100vh - 80px);
  padding: 0;
  margin: 0;
}

.workbench-main.glass-card {
  /* 覆盖通用 glass-card，让整个页面左右分栏铺满 */
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 16px 20px;
  box-sizing: border-box;
  background: transparent;
  border: none;
  box-shadow: none;
  display: flex;
  flex-direction: column;
}

.workbench-columns {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr; /* 左右各占一半 */
  gap: 0;
  min-height: 0;
}

.pane {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.pane h3 {
  margin: 0 0 8px;
  font-size: 13px;
}

.demo-block {
  font-size: 12px;
}
</style>
