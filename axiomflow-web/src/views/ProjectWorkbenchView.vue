<template>
  <section class="workbench">
    <div class="workbench-main glass-card">
      <!-- Demo 项目预期说明 -->
      <div
        v-if="isDemoProject"
        class="app-alert app-alert--info"
        role="status"
        aria-live="polite"
        style="margin-bottom: 12px"
      >
        <div class="app-alert-content">
          <p class="app-alert-title">
            {{ $t("workbench.demoBannerTitle") }}
          </p>
          <p class="app-alert-message">
            {{ $t("workbench.demoBannerDesc") }}
          </p>
        </div>
      </div>
      <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px">
        <div style="display:flex;align-items:center;gap:10px">
          <AppButton 
            @click="goBackToDashboard"
            :aria-label="$t('workbench.backToDocs')"
          >
            {{ $t("workbench.backToDocs") }}
          </AppButton>
          <div style="color:#9ca3af;font-size:12px" aria-label="Document information">
            {{ doc?.document.title }} · {{ doc?.document.lang_in }}→{{ doc?.document.lang_out }}
          </div>
        </div>
        <div style="display:flex;gap:10px;align-items:center">
          <div v-if="jobStatus" style="color:#9ca3af;font-size:12px" role="status" aria-live="polite">
            {{ jobStatus }}
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="workbench-loading" role="status" aria-live="polite" aria-label="Loading document">
        <div class="workbench-loading-spinner"></div>
        <p class="workbench-loading-text">{{ $t("workbench.loading") || "Loading..." }}</p>
      </div>
      
      <!-- 错误状态 -->
      <div v-else-if="error" class="workbench-error" role="alert">
        <div class="workbench-error-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <p class="workbench-error-text">{{ error }}</p>
        <AppButton @click="refresh">{{ $t("workbench.retry") || "Retry" }}</AppButton>
      </div>
      
      <!-- 正常内容 -->
      <div v-else class="workbench-columns">
        <div class="pane pane-original">
          <h3>{{ $t("workbench.sourcePdf") }}</h3>
          <div v-if="doc" class="pane-content">
            <PdfCanvasViewer
              :pdf-url="sourcePdfUrl"
              :page-width="doc.pages[0]?.width || 1000"
              :page-height="doc.pages[0]?.height || 1000"
              :blocks="[] as any"
              :active-block-id="null"
              :continuous="true"
            />
          </div>
          <p v-else class="demo-block" style="color: #9ca3af">{{ $t("workbench.sourcePdfHint") }}</p>
        </div>

        <div class="pane pane-translation">
          <h3>{{ $t("workbench.translatedPdf") }}</h3>
          <div v-if="translatedPdfUrl" class="pane-content">
            <PdfCanvasViewer
              :pdf-url="translatedPdfUrl"
              :page-width="doc?.pages[0]?.width || 1000"
              :page-height="doc?.pages[0]?.height || 1000"
              :blocks="[] as any"
              :active-block-id="null"
              :continuous="true"
            />
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import AppButton from "@/components/AppButton.vue";
import PdfCanvasViewer from "@/components/PdfCanvasViewer.vue";
import { exportDocument, getDocument, getJob, getSourcePdfUrl, getTranslatedPdfUrl, StructuredDoc, translateDocument } from "@/lib/api";

const route = useRoute();
const router = useRouter();
const { t } = useI18n();
const documentId = computed(() => String(route.params.id || ""));
const isDemoProject = computed(() => documentId.value === "demo");

const doc = ref<StructuredDoc | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

const jobStatus = ref<string | null>(null);
const jobId = ref<string | null>(null);
const translating = ref(false);
let refreshTimer: number | null = null;

const sourcePdfUrl = computed(() => (doc.value ? getSourcePdfUrl(doc.value.document.id) : ""));
const translatedPdfUrl = computed(() => {
  if (!doc.value) return "";
  // 检查文档是否有译文PDF路径（解析+翻译完成后会有）
  const translatedPath = doc.value.document.translated_pdf_path;
  if (translatedPath) {
    return getTranslatedPdfUrl(doc.value.document.id);
  }
  return "";
});

const pollJob = async (id: string) => {
  for (let i = 0; i < 240; i++) {
    await new Promise((resolve) => setTimeout(resolve, 800));
    try {
      const j = await getJob(id);
      const pct = Math.round((j?.progress ?? 0) * 100);
      const eta = j?.eta_s != null ? ` · ${t("workbench.eta", { sec: Math.round(j.eta_s) })}` : "";
      const done = j?.done != null && j?.total != null ? ` · ${j.done}/${j.total}` : "";
      jobStatus.value = `${j?.stage ?? "unknown"} · ${pct}%${done}${eta}`;
      if (j?.stage === "success" || j?.stage === "failed" || j?.stage === "canceled") {
        // 任务完成后，刷新文档数据以获取译文PDF
        await refresh();
        break;
      }
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
    // 调试：输出文档信息
    console.log("[ProjectWorkbenchView] 文档刷新:", {
      document_id: doc.value?.document?.id,
      translated_pdf_path: doc.value?.document?.translated_pdf_path,
      status: doc.value?.document?.status,
    });
    
    // 如果文档还在解析中且没有译文PDF，设置定时器定期刷新
    if (doc.value && !doc.value.document.translated_pdf_path) {
      const status = doc.value.document.status;
      if (status === "parsing" || status === "ready") {
        // 文档还在处理中，设置定时器每3秒刷新一次，直到有译文PDF或超过5分钟
        if (refreshTimer) {
          clearInterval(refreshTimer);
        }
        let attempts = 0;
        const maxAttempts = 100; // 最多尝试100次（约5分钟）
        refreshTimer = window.setInterval(async () => {
          attempts++;
          if (attempts >= maxAttempts) {
            if (refreshTimer) {
              clearInterval(refreshTimer);
              refreshTimer = null;
            }
            return;
          }
          try {
            const updatedDoc = await getDocument(documentId.value);
            console.log("[ProjectWorkbenchView] 轮询检查:", {
              document_id: updatedDoc?.document?.id,
              translated_pdf_path: updatedDoc?.document?.translated_pdf_path,
              attempt: attempts,
            });
            if (updatedDoc.document.translated_pdf_path) {
              // 找到译文PDF，更新文档并停止轮询
              console.log("[ProjectWorkbenchView] 找到译文PDF，停止轮询");
              doc.value = updatedDoc;
              if (refreshTimer) {
                clearInterval(refreshTimer);
                refreshTimer = null;
              }
            }
          } catch (err) {
            // 忽略刷新错误，继续轮询
            console.warn("[ProjectWorkbenchView] 轮询刷新失败:", err);
          }
        }, 3000); // 每3秒刷新一次
      }
    } else if (refreshTimer) {
      // 如果已经有译文PDF，停止轮询
      console.log("[ProjectWorkbenchView] 已有译文PDF，停止轮询");
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    loading.value = false;
  }
};

// 注意：翻译现在在解析阶段自动完成，不再需要手动触发
// 保留此函数以防需要手动重新翻译
const runTranslateAndExport = async () => {
  if (!doc.value || translating.value) return;
  translating.value = true;
  try {
    // 使用 Google 翻译
    const { job_id } = await translateDocument({
      document_id: doc.value.document.id,
      lang_in: doc.value.document.lang_in,
      lang_out: doc.value.document.lang_out,
      provider: "google", // 明确指定使用 Google 翻译
    });
    jobId.value = job_id;
    await pollJob(job_id);
    
    // 翻译完成后，刷新文档数据以获取最新翻译结果
    await refresh();
    
    // 导出译文PDF（单语版本，显示在右侧）
    const res: any = await exportDocument({
      document_id: doc.value.document.id,
      format: "pdf-mono" as any, // 使用单语版本，只显示译文
      bilingual: false,
      subset_fonts: true,
      convert_to_pdfa: false,
    });
    if (res?.download_url) {
      // 更新文档JSON中的译文PDF路径（如果需要）
      await refresh();
    }
  } finally {
    translating.value = false;
  }
};

const goBackToDashboard = () => {
  router.push({ name: "dashboard" });
};

onMounted(refresh);
watch(documentId, () => {
  // 切换文档时，清除之前的定时器
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
  refresh();
});

// 组件卸载时清除定时器
onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
});
</script>

<style scoped>
.workbench {
  display: flex;
  /* 使用固定高度，防止整个页面滚动，增加高度让卡片更长 */
  height: calc(100vh - 60px);
  padding: 0;
  margin: 0;
  overflow: hidden;
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
  height: 100%;
  overflow: hidden;
}

.pane {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  min-height: 0;
}

.pane h3 {
  margin: 0 0 8px;
  font-size: 13px;
  flex-shrink: 0;
}

.pane-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
  height: 100%;
  width: 100%;
}

.demo-block {
  font-size: 12px;
}

/* Workbench 加载和错误状态 */
.workbench-loading,
.workbench-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 48px 24px;
  text-align: center;
}

.workbench-loading-spinner {
  width: 48px;
  height: 48px;
  border: 3px solid rgba(99, 102, 241, 0.2);
  border-top-color: var(--color-primary, #6366f1);
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
  margin-bottom: 16px;
}

.workbench-loading-text {
  color: var(--color-text-muted, #64748b);
  font-size: 14px;
}

.workbench-error {
  gap: 16px;
}

.workbench-error-icon {
  width: 64px;
  height: 64px;
  color: var(--color-danger, #ef4444);
  margin-bottom: 8px;
}

.workbench-error-text {
  color: var(--color-text, #1e293b);
  font-size: 16px;
  max-width: 500px;
}

[data-theme="dark"] .workbench-loading-text {
  color: var(--color-text-muted, #9ca3af);
}

[data-theme="dark"] .workbench-error-text {
  color: var(--color-text, #e5e7eb);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .workbench-loading,
  .workbench-error {
    min-height: 300px;
    padding: 32px 16px;
  }
  
  .workbench-loading-spinner {
    width: 40px;
    height: 40px;
  }
  
  .workbench-error-icon {
    width: 48px;
    height: 48px;
  }
}
</style>
