<template>
  <section class="dashboard">
    <!-- 安全向导弹窗：登录后针对未验证邮箱的一次性提示 -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showSecurityGuide"
          class="modal-overlay"
          @click.self="closeSecurityGuide"
          role="dialog"
          aria-modal="true"
          aria-labelledby="security-guide-title"
        >
          <div class="modal-content glass-card security-guide-modal">
            <div class="modal-header">
              <h2 id="security-guide-title">账户安全建议</h2>
              <button class="modal-close" @click="closeSecurityGuide" aria-label="关闭">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </button>
            </div>
            <div class="modal-body">
              <p class="modal-description">
                当前账户邮箱尚未完成验证，建议先完成邮箱验证，并在设置中开启双因素认证（2FA），以提升账户安全性。
              </p>
              <ul class="security-guide-list">
                <li>1. 前往「设置 &gt; 安全」检查邮箱验证状态，如未收到邮件可重新发送验证邮件。</li>
                <li>2. 建议开启 2FA（基于验证码的双因素认证），防止密码泄露后被他人登录。</li>
                <li>3. 定期检查「活跃会话」列表，及时撤销不认识的设备登录。</li>
              </ul>
              <div class="security-guide-actions">
                <button class="security-guide-primary" @click="goToSecuritySettings">
                  前往安全设置
                </button>
                <button class="security-guide-secondary" @click="closeSecurityGuide">
                  暂时跳过
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 邮箱验证提示横幅 -->
    <div v-if="userStore.user && !userStore.user.email_verified" class="email-verification-banner">
      <div class="email-verification-content">
        <div class="email-verification-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="22,6 12,13 2,6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="email-verification-text">
          <strong>请验证您的邮箱地址</strong>
          <span>未验证账户将限制部分功能，请检查您的邮箱并点击验证链接完成验证。</span>
        </div>
        <div class="email-verification-actions">
          <button class="email-verification-btn" @click="handleResendVerification" :disabled="resendingVerification">
            <span v-if="resendingVerification" class="loading-spinner-small"></span>
            <span>{{ resendingVerification ? "发送中..." : "重新发送验证邮件" }}</span>
          </button>
        </div>
      </div>
    </div>
    <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px">
      <h2 style="margin: 0">我的文档</h2>
      <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap">
        <button
          class="dashboard-refresh-icon-btn"
          :class="{ 'is-spinning': isRefreshingList }"
          :disabled="isRefreshingList"
          title="刷新列表"
          @click="refreshList"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path
              d="M20 12a8 8 0 10-2.343 5.657"
              stroke="currentColor"
              stroke-width="2"
              fill="none"
              stroke-linecap="round"
            />
            <path
              d="M20 8v4h-4"
              stroke="currentColor"
              stroke-width="2"
              fill="none"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </button>
        <div class="dashboard-search">
          <span class="dashboard-search-icon">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="11" cy="11" r="6" stroke="currentColor" stroke-width="1.8" fill="none" />
              <line x1="16" y1="16" x2="21" y2="21" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
            </svg>
          </span>
          <input
            class="simple-input dashboard-search-input"
            v-model="searchQuery"
            placeholder="搜索文件名…"
          />
        </div>
        <AppButton class="action-btn" @click="pickFile">上传PDF（单个）</AppButton>
        <AppButton class="action-btn action-btn--gradient" @click="pickFiles">批量上传PDF</AppButton>
        <AppButton 
          v-if="selectedDocuments.size > 0"
          class="action-btn action-btn--danger"
          @click="handleBatchDelete"
        >
          批量删除 ({{ selectedDocuments.size }})
        </AppButton>
        <AppButton 
          v-if="isSelectionMode"
          @click="exitSelectionMode"
          class="action-btn action-btn--muted"
        >
          取消选择
        </AppButton>
        <AppButton 
          v-else-if="docs.length > 0"
          @click="enterSelectionMode"
          class="action-btn action-btn--primary"
        >
          批量选择
        </AppButton>
        <input ref="fileInput" type="file" accept="application/pdf" style="display: none" @change="onFileChange" />
        <input ref="filesInput" type="file" accept="application/pdf" multiple style="display: none" @change="onFilesChange" />
      </div>
    </div>
    <div class="empty-state" v-if="docs.length === 0">
      <div class="empty-state-content">
        <div class="empty-state-icon">
          <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 14C18 12.8954 18.8954 12 20 12H44C45.1046 12 46 12.8954 46 14V42C46 43.1046 45.1046 44 44 44H20C18.8954 44 18 43.1046 18 42V14Z" stroke="url(#emptyGradient)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
            <path d="M22 20H42M22 26H36M22 32H42" stroke="url(#emptyGradient)" stroke-width="2.5" stroke-linecap="round"/>
            <path d="M22 38H36" stroke="url(#emptyGradient)" stroke-width="2.5" stroke-linecap="round" opacity="0.6"/>
            <circle cx="50" cy="18" r="3" fill="url(#emptyGradient)" opacity="0.8"/>
            <defs>
              <linearGradient id="emptyGradient" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stop-color="#3b82f6"/>
                <stop offset="100%" stop-color="#8b5cf6"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h3 class="empty-state-title">暂无文档</h3>
        <p class="empty-state-description">开始上传您的第一个 PDF 文档，让我们帮您解析和翻译</p>
      </div>
    </div>
    <div v-else-if="filteredDocs.length === 0" class="empty-state">
      <div class="empty-state-content">
        <div class="empty-state-icon">
          <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="28" cy="28" r="12" stroke="url(#emptySearchGradient)" stroke-width="2.5" fill="none"/>
            <line x1="36" y1="36" x2="48" y2="48" stroke="url(#emptySearchGradient)" stroke-width="2.5" stroke-linecap="round"/>
            <defs>
              <linearGradient id="emptySearchGradient" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stop-color="#3b82f6"/>
                <stop offset="100%" stop-color="#8b5cf6"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h3 class="empty-state-title">未找到匹配的文件名</h3>
        <p class="empty-state-description">尝试修改关键字，或清除搜索条件查看全部文档。</p>
        <AppButton class="action-btn action-btn--muted" @click="clearSearch">
          清除搜索条件
        </AppButton>
      </div>
    </div>
    <div class="card-grid" v-else>
      <AppCard
        v-for="d in filteredDocs"
        :key="d.document_id"
        class="doc-card"
        :class="{ 
          'doc-card--parsing': d.status === 'parsing', 
          'doc-card--ready': d.status === 'ready',
          'doc-card--selected': isSelectionMode && selectedDocuments.has(d.document_id)
        }"
        @click="isSelectionMode ? toggleDocumentSelection(d.document_id) : (d.status === 'ready' ? openDoc(d.document_id) : undefined)"
      >
        <!-- 选择复选框（选择模式下显示） -->
        <div v-if="isSelectionMode && d.status === 'ready' && !d.document_id.startsWith('temp-')" class="doc-checkbox-container">
          <input
            type="checkbox"
            :checked="selectedDocuments.has(d.document_id)"
            @click.stop="toggleDocumentSelection(d.document_id)"
            class="doc-checkbox"
          />
        </div>
        <!-- 缩略图区域（所有状态都显示） -->
        <div class="doc-thumbnail-container" :class="{ 'doc-thumbnail-container--processing': d.status !== 'ready' }">
          <img 
            v-if="d.document_id && !d.document_id.startsWith('temp-') && !d.thumbnailError"
            :src="getThumbnailUrl(d.document_id)" 
            :alt="d.title"
            class="doc-thumbnail"
            :class="{ 'doc-thumbnail--loading': d.status !== 'ready' }"
            @error="(e) => handleThumbnailError(e, d.document_id)"
            @load="handleThumbnailLoad(d.document_id)"
          />
          <div v-else class="doc-thumbnail-placeholder">
            <LoadingIcon :spinning="d.status !== 'ready'" />
          </div>
          <!-- 解析中的遮罩层 -->
          <div v-if="d.status !== 'ready'" class="doc-thumbnail-overlay">
            <div class="doc-processing-badge">
              <span v-if="d.status === 'uploading'">上传中</span>
              <span v-else-if="d.status === 'parsing'">解析中</span>
            </div>
          </div>
          <!-- 删除按钮（右上角，非选择模式下显示） -->
          <button
            v-if="!isSelectionMode && d.status === 'ready' && !d.document_id.startsWith('temp-')"
            class="doc-delete-button"
            @click.stop="handleDeleteDocument(d.document_id, d.title)"
            :disabled="deletingDocumentId === d.document_id"
            title="删除文档"
          >
            <svg v-if="deletingDocumentId !== d.document_id" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 6H5H21M8 6V4C8 3.46957 8.21071 2.96086 8.58579 2.58579C8.96086 2.21071 9.46957 2 10 2H14C14.5304 2 15.0391 2.21071 15.4142 2.58579C15.7893 2.96086 16 3.46957 16 4V6M19 6V20C19 20.5304 18.7893 21.0391 18.4142 21.4142C18.0391 21.7893 17.5304 22 17 22H7C6.46957 22 5.96086 21.7893 5.58579 21.4142C5.21071 21.0391 5 20.5304 5 20V6H19Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <LoadingIcon v-else :spinning="true" />
          </button>
        </div>
        
        <!-- 进度条（解析中/上传中时显示） -->
        <div v-if="d.status === 'uploading' || d.status === 'parsing'" class="doc-progress-section">
          <div class="progress-bar-wrapper">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: `${d.progress || 0}%` }"></div>
            </div>
            <div class="progress-text">
              <span v-if="d.status === 'uploading'">上传中... {{ formatProgress(d.progress) }}%</span>
              <span v-else-if="d.status === 'parsing'">
                解析中... {{ formatProgress(d.progress) }}%
              </span>
            </div>
          </div>
        </div>
        
        <!-- 底部信息（所有状态都显示） -->
        <div class="doc-footer">
          <div class="doc-title-footer">{{ d.title }}</div>
          <div class="doc-meta-footer">
            <span v-if="d.status === 'uploading'">
              正在上传中...
            </span>
            <span v-else-if="d.status === 'parsing'">
              <span v-if="d.num_pages && d.num_pages > 0">{{ d.num_pages }} 页 · </span>解析中...
            </span>
            <span v-else>
              {{ d.num_pages || '?' }} 页 · {{ d.lang_in }} → {{ d.lang_out }} · 已解析
            </span>
          </div>
        </div>
      </AppCard>
    </div>
    <!-- 删除确认对话框 -->
    <ConfirmDialog
      v-model:visible="showDeleteDialog"
      :title="deleteDialogTitle"
      :message="deleteDialogMessage"
      type="danger"
      confirm-text="删除"
      cancel-text="取消"
      :loading="deletingDocumentId !== null"
      @confirm="confirmDeleteDocument"
      @cancel="cancelDeleteDocument"
    />
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref, watch, onUnmounted, nextTick, computed } from "vue";
import AppCard from "@/components/AppCard.vue";
import AppButton from "@/components/AppButton.vue";
import LoadingIcon from "@/components/LoadingIcon.vue";
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import { batchUpload, createProject, uploadPdf, getDocument, getProjectDocuments, getUserDocuments, deleteDocument, batchDeleteDocuments, sendEmailVerification } from "@/lib/api";
import { showToast } from "@/components/Toast";
import { useRouter, useRoute } from "vue-router";
import { DocumentProgressWebSocket } from "@/lib/websocket";
import { useUserStore } from "@/stores/user";

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

type DocStatus = "uploading" | "parsing" | "ready";

interface Doc {
  document_id: string;
  title: string;
  num_pages?: number;
  lang_in: string;
  lang_out: string;
  status: DocStatus;
  progress: number;
  parse_done?: number;
  parse_total?: number;
  parse_eta_s?: number;
  parse_message?: string;
  parse_substage?: string;
  thumbnailError?: boolean; // 缩略图加载失败标志
}

const formatProgress = (p: number | undefined | null) => {
  const n = typeof p === "number" && Number.isFinite(p) ? p : 0;
  return n.toFixed(2);
};

const formatEta = (eta_s: number | undefined | null) => {
  const n = typeof eta_s === "number" && Number.isFinite(eta_s) ? Math.max(0, eta_s) : null;
  if (n === null) return "";
  const sec = Math.round(n);
  if (sec < 60) return `${sec}s`;
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  if (m < 60) return `${m}m ${s}s`;
  const h = Math.floor(m / 60);
  const mm = m % 60;
  return `${h}h ${mm}m`;
};

const DEBUG = import.meta.env.DEV;
const LANG_IN_DEFAULT = "en";
const LANG_OUT_DEFAULT = "zh";
const debugLog = (...args: any[]) => {
  if (DEBUG) console.log(...args);
};
const debugWarn = (...args: any[]) => {
  if (DEBUG) console.warn(...args);
};

const docs = ref<Doc[]>([]);
const searchQuery = ref("");
const debouncedSearchQuery = ref("");
let searchDebounceTimer: number | undefined;
const fileInput = ref<HTMLInputElement | null>(null);
const filesInput = ref<HTMLInputElement | null>(null);
const projectName = ref("我的项目");
const currentProjectId = ref<string | null>(null); // 当前项目ID
const activeWebSockets = new Map<string, DocumentProgressWebSocket>(); // document_id -> WebSocket
const parsingStartAt = new Map<string, number>(); // document_id -> 首次解析开始时间
const parsingWarned = new Set<string>(); // 已提示解析过长的文档
let parsingMonitorTimer: number | undefined;
const PARSING_WARN_THRESHOLD_MS = 2 * 60 * 1000; // 解析超过2分钟提示
const deletingDocumentId = ref<string | null>(null); // 正在删除的文档ID
const showDeleteDialog = ref(false); // 显示删除确认对话框
const deleteDialogTitle = ref(""); // 删除对话框标题
const deleteDialogMessage = ref(""); // 删除对话框消息
const pendingDeleteDocumentId = ref<string | null>(null); // 待删除的文档ID
const pendingDeleteTitle = ref(""); // 待删除的文档标题
const isSelectionMode = ref(false); // 是否处于选择模式
const selectedDocuments = ref<Set<string>>(new Set()); // 选中的文档ID集合
const isBatchDelete = ref(false); // 是否是批量删除
//（已移除卡片内“刷新状态”按钮，仅保留右上角刷新列表 icon）
const isRefreshingList = ref(false); // 右上角刷新列表按钮状态
const resendingVerification = ref(false); // 重新发送验证邮件状态

// 安全向导：仅在登录后且邮箱未验证时给出一次性弹窗提示
const showSecurityGuide = ref(false);
const SECURITY_GUIDE_SEEN_KEY = "security_guide_seen_v1";

const maybeShowSecurityGuide = () => {
  if (!userStore.user || userStore.user.email_verified) return;
  if (localStorage.getItem(SECURITY_GUIDE_SEEN_KEY) === "1") return;
  showSecurityGuide.value = true;
};

const closeSecurityGuide = () => {
  showSecurityGuide.value = false;
  localStorage.setItem(SECURITY_GUIDE_SEEN_KEY, "1");
};

const goToSecuritySettings = () => {
  closeSecurityGuide();
  router.push({ path: "/settings", query: { from: "dashboard_security_guide" } });
};

// Dashboard 顶部搜索快捷键处理：/、Ctrl/Cmd+F 聚焦搜索框，Esc 清空搜索与选择
const keyHandler = (e: KeyboardEvent) => {
  const target = e.target as HTMLElement | null;
  const isEditableTarget =
    target &&
    (target.tagName === "INPUT" ||
      target.tagName === "TEXTAREA" ||
      (target as HTMLElement).isContentEditable ||
      target.tagName === "SELECT");
  if (isEditableTarget) return;
  // 聚焦搜索：/ 或 Ctrl/Cmd+F
  if (
    (e.key === "/" && !e.ctrlKey && !e.metaKey && !e.altKey) ||
    (e.key.toLowerCase() === "f" && (e.ctrlKey || e.metaKey))
  ) {
    e.preventDefault();
    const input = document.querySelector(".dashboard-search-input") as HTMLInputElement | null;
    input?.focus();
    return;
  }
  // Esc 清空搜索并清理选择
  if (e.key === "Escape") {
    if (searchQuery.value) {
      searchQuery.value = "";
    }
    selectedDocuments.value.clear();
    return;
  }
};

const filteredDocs = computed(() => {
  const q = debouncedSearchQuery.value.trim().toLowerCase();
  if (!q) return docs.value;
  return docs.value.filter((d) => (d.title || "").toLowerCase().includes(q));
});

const clearSearch = () => {
  searchQuery.value = "";
  selectedDocuments.value.clear();
};

// 搜索与选择状态联动 & 200ms 防抖
watch(
  searchQuery,
  (val) => {
    // 清空已选文档，避免“隐身选中项”
    selectedDocuments.value.clear();
    // 输入搜索时自动退出选择模式
    if (val && isSelectionMode.value) {
      isSelectionMode.value = false;
    }
    // 防抖更新实际用于过滤的关键字
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
    }
    searchDebounceTimer = window.setTimeout(() => {
      debouncedSearchQuery.value = val;
    }, 200);
  }
);

const updateDoc = (document_id: string, patch: Partial<Doc>) => {
  const idx = docs.value.findIndex((d) => d.document_id === document_id);
  if (idx >= 0) {
    docs.value.splice(idx, 1, { ...docs.value[idx], ...patch });
  }
};

const refreshList = async () => {
  if (isRefreshingList.value) return;
  isRefreshingList.value = true;
  try {
    const pid = currentProjectId.value;
    if (pid) {
      await loadProjectDocuments(pid, true);
    } else {
      await loadUserDocuments(true);
    }
    showToast("success", "已刷新", "文档列表已更新");
  } catch (e: any) {
    showToast("error", "刷新失败", e?.message || "请稍后重试");
  } finally {
    isRefreshingList.value = false;
  }
};

const finalizeReady = async (
  document_id: string,
  options: { numPagesHint?: number; projectId?: string; ws?: DocumentProgressWebSocket } = {}
) => {
  const idx = docs.value.findIndex((d) => d.document_id === document_id);
  if (idx < 0) return;
  let shouldDisconnect = false;
  try {
    const docData = await getDocument(document_id);
    const document = docData.document;
    const isParsed = document?.status === "parsed" || document?.status === "ready";
    if (isParsed) {
      updateDoc(document_id, {
        title: document.title || docs.value[idx].title,
        num_pages: document.num_pages ?? options.numPagesHint ?? docs.value[idx].num_pages,
        lang_in: document.lang_in || docs.value[idx].lang_in,
        lang_out: document.lang_out || docs.value[idx].lang_out,
        status: "ready",
        progress: 100,
      });
      shouldDisconnect = true;
    } else {
      // 后端尚未准备好，保持 parsing 状态
      updateDoc(document_id, {
        status: "parsing",
        progress: Math.max(docs.value[idx].progress || 0, 90),
      });
      showToast("info", "后台同步中", "解析结果尚未生成，请稍后刷新");
      return;
    }
  } catch (error) {
    debugWarn("finalizeReady getDocument failed:", error);
    if (options.numPagesHint !== undefined) {
      updateDoc(document_id, {
        status: "ready",
        progress: 100,
        num_pages: options.numPagesHint,
      });
      shouldDisconnect = true;
    } else {
      showToast("warning", "状态未更新", "尚未获取到解析结果，请稍后重试或刷新状态");
      return;
    }
  } finally {
    if (shouldDisconnect) {
      options.ws?.disconnect();
      activeWebSockets.delete(document_id);
      parsingStartAt.delete(document_id);
      parsingWarned.delete(document_id);
      const pid = options.projectId || currentProjectId.value;
      if (pid) {
        await loadProjectDocuments(pid, true);
      }
      router.replace({ query: {} });
    }
  }
};

const handleProgressMessage = async (params: {
  document_id: string;
  data: any;
  startTime?: number;
  projectId?: string;
  ws?: DocumentProgressWebSocket;
}) => {
  const { document_id, data, projectId, ws } = params;
  const idx = docs.value.findIndex((d) => d.document_id === document_id);
  if (idx < 0) {
    debugWarn(`文档 ${document_id} 不在列表中`);
    return;
  }
  const currentDoc = docs.value[idx];
  const clamp = (n: number, min: number, max: number) => Math.max(min, Math.min(max, n));
  const normalizePercent01or100 = (v: any): number | undefined => {
    if (v === undefined || v === null) return undefined;
    const n = typeof v === "number" ? v : Number(v);
    if (!Number.isFinite(n)) return undefined;
    // 兼容 0~1 或 0~100
    if (n >= 0 && n <= 1) return n * 100;
    return n;
  };

  if (data.status === "uploading") {
    // uploading 阶段仅展示 0~30%，兼容 parse_progress 可能是 0~1 或 0~100
    const raw = normalizePercent01or100(data.parse_progress);
    const base = raw !== undefined ? raw : (currentDoc.progress || 0);
    const targetProgress = clamp(base, 0, 30);
    updateDoc(document_id, { status: "uploading", progress: Math.max(currentDoc.progress || 0, targetProgress) });
    debugLog(`[上传中] 进度: ${targetProgress.toFixed(2)}%`);
    return;
  }

  if (data.status === "parsing") {
    if (!parsingStartAt.has(document_id)) {
      parsingStartAt.set(document_id, Date.now());
    }
    let targetProgress: number | undefined = undefined;
    let patchExtraFromJob: Partial<Doc> | undefined;
    if (data.parse_job) {
      const parseJob = data.parse_job;
      if (parseJob.total && parseJob.total > 0) {
        const parseProgress = (parseJob.done || 0) / parseJob.total;
        targetProgress = 30 + clamp(parseProgress, 0, 1) * 70;
        debugLog(`[解析中] 使用 Job 进度: ${parseJob.done}/${parseJob.total} = ${parseProgress}, 目标进度: ${targetProgress.toFixed(2)}%`);
      } else {
        const raw = normalizePercent01or100(parseJob.progress);
        if (raw !== undefined) {
          targetProgress = 30 + clamp(raw / 100, 0, 1) * 70;
          debugLog(`[解析中] 使用 Job progress 字段: ${parseJob.progress}, 目标进度: ${targetProgress.toFixed(2)}%`);
        }
      }
      // 将更“真实”的动态信息同步到卡片上（页数进度/ETA/消息）
      patchExtraFromJob = {
        parse_done: typeof parseJob.done === "number" ? parseJob.done : undefined,
        parse_total: typeof parseJob.total === "number" ? parseJob.total : undefined,
        parse_eta_s: typeof parseJob.eta_s === "number" ? parseJob.eta_s : undefined,
        parse_message: typeof parseJob.message === "string" ? parseJob.message : undefined,
        parse_substage: typeof parseJob.substage === "string" ? parseJob.substage : undefined,
      };
    } else if (data.parse_progress !== undefined && data.parse_progress !== null) {
      const raw = normalizePercent01or100(data.parse_progress);
      if (raw !== undefined) {
        const parseProgressPercent = clamp(raw, 0, 100) / 100;
        targetProgress = 30 + parseProgressPercent * 70;
        debugLog(`[解析中] 使用 parse_progress: ${data.parse_progress}% -> ${parseProgressPercent}, 目标进度: ${targetProgress.toFixed(2)}%`);
      }
    }
    // 兜底：后端不提供进度字段时，按时间缓慢推进到 90%，避免卡在 30%
    if (targetProgress === undefined) {
      const started = parsingStartAt.get(document_id) || Date.now();
      const elapsed = Date.now() - started;
      // 约 35s 从 30% 推进到 90%，再等待 parsed
      const fallback = 30 + clamp(elapsed / 35000, 0, 1) * 60;
      targetProgress = fallback;
      debugLog("[解析中] 无进度字段，使用兜底平滑进度:", targetProgress.toFixed(2));
    }
    // 不允许倒退，且 parsing 阶段最多展示到 99%
    targetProgress = clamp(targetProgress, 30, 99);
    const patch: Partial<Doc> = { status: "parsing", progress: targetProgress, ...(patchExtraFromJob || {}) };
    if (data.num_pages !== undefined && data.num_pages > 0) {
      patch.num_pages = data.num_pages;
    }
    patch.progress = Math.max(currentDoc.progress || 0, patch.progress || 0);
    updateDoc(document_id, patch);
    return;
  }

  if (data.status === "parsed" || data.status === "ready") {
    const hinted = typeof data.num_pages === "number" ? data.num_pages : undefined;
    if (!hinted || hinted <= 0) {
      debugLog(`收到 parsed/ready 但页数未就绪 (${document_id}): num_pages=${data.num_pages}，进入后台写入等待`);
      updateDoc(document_id, { status: "parsing", progress: Math.max(currentDoc.progress || 0, 99) });
    } else {
      debugLog(`解析完成 (${document_id}): num_pages=${data.num_pages}`);
    }
    await finalizeReady(document_id, { numPagesHint: hinted, projectId, ws });
    return;
  }
};

const attachProgressWS = (document_id: string, options: { projectId?: string } = {}) => {
  const ws = new DocumentProgressWebSocket(document_id);
  activeWebSockets.set(document_id, ws);
  ws.onMessage((data) => handleProgressMessage({ document_id, data, projectId: options.projectId, ws }));
  ws.onError((error) => {
    debugWarn("WebSocket 错误:", error);
    updateDoc(document_id, { status: "parsing", progress: Math.max((docs.value.find(d => d.document_id === document_id)?.progress || 0), 50) });
    showToast("warning", "实时进度连接异常", "文档实时进度可能无法更新，可稍后刷新查看。");
  });
  ws.onClose(() => {
    activeWebSockets.delete(document_id);
  });
  ws.connect().catch((error) => {
    debugWarn("WebSocket 连接失败:", error);
    showToast("warning", "实时进度连接失败", "文档上传已开始，但实时进度连接中断，可稍后刷新查看状态。");
  });
  return ws;
};

// 从 API 加载项目文档列表（合并模式：保留正在处理的临时文档）
const loadProjectDocuments = async (project_id: string, merge: boolean = false) => {
  try {
    const response = await getProjectDocuments(project_id);
    // 将 API 返回的文档转换为前端格式
    const apiDocs = response.documents.map((d) => ({
      document_id: d.document_id,
      title: d.title,
      num_pages: d.num_pages,
      lang_in: d.lang_in,
      lang_out: d.lang_out,
      status: d.status === "parsed" ? "ready" : (d.status === "parsing" ? "parsing" : "ready") as DocStatus,
      progress: d.status === "parsed" ? 100 : 0,
      thumbnailError: false, // 默认没有错误
    }));
    
    if (merge) {
      // 合并模式：仅保留正在处理的临时文档（uploading/parsing 状态）和真正的临时卡片
      const tempDocs = docs.value.filter(d =>
        d.status === "uploading" ||
        d.status === "parsing" ||
        d.document_id.startsWith("temp-")
      );
      // 合并 API 文档和临时文档，去重（ready 文档以 API 为准）
      const existingIds = new Set(tempDocs.map(d => d.document_id));
      const newDocs = apiDocs.filter(d => !existingIds.has(d.document_id));
      const mergedDocs = tempDocs.map(localDoc => {
        const apiDoc = apiDocs.find(api => api.document_id === localDoc.document_id);
        // 使用 API 返回的最新状态（但保留本地的 progress 等信息）
        return apiDoc ? { ...apiDoc, progress: localDoc.progress || apiDoc.progress } : localDoc;
      });
      docs.value = [...mergedDocs, ...newDocs];
    } else {
      // 完全替换模式
      docs.value = apiDocs;
    }
    currentProjectId.value = project_id;
  } catch (error) {
    console.error("加载文档列表失败:", error);
    // 如果项目不存在或加载失败，且不是合并模式，才清空列表
    if (!merge) {
      docs.value = [];
    }
  }
};

// 加载用户的所有文档（不依赖项目）
const loadUserDocuments = async (merge: boolean = false) => {
  try {
    const response = await getUserDocuments();
    // 将 API 返回的文档转换为前端格式
    const apiDocs = response.documents.map((d) => ({
      document_id: d.document_id,
      title: d.title,
      num_pages: d.num_pages,
      lang_in: d.lang_in,
      lang_out: d.lang_out,
      status: d.status === "parsed" ? "ready" : (d.status === "parsing" ? "parsing" : "ready") as DocStatus,
      progress: d.status === "parsed" ? 100 : 0,
      thumbnailError: false, // 默认没有错误
    }));
    
    if (merge) {
      // 合并模式：仅保留正在处理的临时文档（uploading/parsing 状态）和真正的临时卡片
      const tempDocs = docs.value.filter(d =>
        d.status === "uploading" ||
        d.status === "parsing" ||
        d.document_id.startsWith("temp-")
      );
      // 合并 API 文档和临时文档，去重（ready 文档以 API 为准）
      const existingIds = new Set(tempDocs.map(d => d.document_id));
      const newDocs = apiDocs.filter(d => !existingIds.has(d.document_id));
      const mergedDocs = tempDocs.map(localDoc => {
        const apiDoc = apiDocs.find(api => api.document_id === localDoc.document_id);
        // 使用 API 返回的最新状态（但保留本地的 progress 等信息）
        return apiDoc ? { ...apiDoc, progress: localDoc.progress || apiDoc.progress } : localDoc;
      });
      docs.value = [...mergedDocs, ...newDocs];
    } else {
      // 完全替换模式
      docs.value = apiDocs;
    }
    
    // 如果文档列表不为空，使用第一个文档的项目ID作为当前项目ID
    if (apiDocs.length > 0 && response.documents[0].project_id) {
      currentProjectId.value = response.documents[0].project_id;
    }
  } catch (error) {
    console.error("加载用户文档列表失败:", error);
    // 如果加载失败，且不是合并模式，才清空列表
    if (!merge) {
      docs.value = [];
    }
  }
};

const pickFile = () => {
  // 检查邮箱验证状态
  if (userStore.user && !userStore.user.email_verified) {
    showToast("warning", "请先验证邮箱", "未验证账户无法上传文档，请先验证您的邮箱地址。");
    return;
  }
  fileInput.value?.click();
};

const pickFiles = () => {
  // 检查邮箱验证状态
  if (userStore.user && !userStore.user.email_verified) {
    showToast("warning", "请先验证邮箱", "未验证账户无法上传文档，请先验证您的邮箱地址。");
    return;
  }
  filesInput.value?.click();
};

const handleResendVerification = async () => {
  if (!userStore.user?.email) {
    showToast("error", "错误", "无法获取邮箱地址");
    return;
  }
  
  resendingVerification.value = true;
  try {
    const result = await sendEmailVerification({ email: userStore.user.email });
    showToast("success", "发送成功", result.message);
    if (result.verification_url) {
      showToast("info", "开发环境提示", `验证链接：${result.verification_url}`);
    }
  } catch (err: any) {
    showToast("error", "发送失败", err.message);
  } finally {
    resendingVerification.value = false;
  }
};

// 获取缩略图URL
const getThumbnailUrl = (document_id: string) => {
  const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000/v1';
  // 增加缩略图尺寸，使其更大
  return `${apiBase}/documents/${document_id}/thumbnail?width=400&height=500`;
};

// 处理缩略图加载错误
const handleThumbnailError = (event: Event, document_id: string) => {
  const img = event.target as HTMLImageElement;
  // 如果缩略图加载失败，标记错误并隐藏图片
  if (img) {
    img.style.display = 'none';
  }
  // 更新文档的缩略图错误标志
  const docIndex = docs.value.findIndex(d => d.document_id === document_id);
  if (docIndex >= 0) {
    docs.value.splice(docIndex, 1, {
      ...docs.value[docIndex],
      thumbnailError: true,
    });
  }
};

// 处理缩略图加载成功
const handleThumbnailLoad = (document_id: string) => {
  // 清除缩略图错误标志
  const docIndex = docs.value.findIndex(d => d.document_id === document_id);
  if (docIndex >= 0 && docs.value[docIndex].thumbnailError) {
    docs.value.splice(docIndex, 1, {
      ...docs.value[docIndex],
      thumbnailError: false,
    });
  }
};

// 删除文档 - 显示确认对话框
const handleDeleteDocument = (document_id: string, title: string) => {
  pendingDeleteDocumentId.value = document_id;
  pendingDeleteTitle.value = title;
  deleteDialogTitle.value = "确认删除文档";
  deleteDialogMessage.value = `确定要删除文档 "${title}" 吗？此操作无法撤销，文档及其所有相关数据将被永久删除。`;
  showDeleteDialog.value = true;
};


// 取消删除
const cancelDeleteDocument = () => {
  pendingDeleteDocumentId.value = null;
  pendingDeleteTitle.value = "";
  isBatchDelete.value = false;
};

// 进入选择模式
const enterSelectionMode = () => {
  isSelectionMode.value = true;
  selectedDocuments.value.clear();
};

// 退出选择模式
const exitSelectionMode = () => {
  isSelectionMode.value = false;
  selectedDocuments.value.clear();
};

// 切换文档选择状态（仅允许 ready 且非临时文档）
const toggleDocumentSelection = (document_id: string) => {
  const doc = docs.value.find((d) => d.document_id === document_id);
  if (!doc) return;
  if (doc.status !== "ready") return;
  if (doc.document_id.startsWith("temp-")) return;

  if (selectedDocuments.value.has(document_id)) {
    selectedDocuments.value.delete(document_id);
  } else {
    selectedDocuments.value.add(document_id);
  }
};

// 批量删除文档
const handleBatchDelete = () => {
  if (selectedDocuments.value.size === 0) return;
  
  const count = selectedDocuments.value.size;
  isBatchDelete.value = true;
  deleteDialogTitle.value = "确认批量删除";
  deleteDialogMessage.value = `确定要删除选中的 ${count} 个文档吗？此操作无法撤销，文档及其所有相关数据将被永久删除。`;
  showDeleteDialog.value = true;
};

// 确认删除（单个或批量）
const confirmDeleteDocument = async () => {
  if (isBatchDelete.value) {
    await confirmBatchDelete();
  } else {
    await confirmSingleDelete();
  }
};

// 确认单个删除
const confirmSingleDelete = async () => {
  if (!pendingDeleteDocumentId.value) return;
  
  const document_id = pendingDeleteDocumentId.value;
  const title = pendingDeleteTitle.value;
  
  deletingDocumentId.value = document_id;
  try {
    await deleteDocument(document_id);
    showToast("success", "删除成功", `文档 "${title}" 已删除`);
    
    // 从列表中移除文档
    const docIndex = docs.value.findIndex(d => d.document_id === document_id);
    if (docIndex >= 0) {
      docs.value.splice(docIndex, 1);
    }
    
    // 关闭相关的 WebSocket 连接
    const ws = activeWebSockets.get(document_id);
    if (ws) {
      ws.close();
      activeWebSockets.delete(document_id);
    }
    
    // 关闭对话框
    showDeleteDialog.value = false;
    pendingDeleteDocumentId.value = null;
    pendingDeleteTitle.value = "";
  } catch (error: any) {
    showToast("error", "删除失败", error.message || "请稍后重试");
  } finally {
    deletingDocumentId.value = null;
  }
};

// 确认批量删除
const confirmBatchDelete = async () => {
  if (selectedDocuments.value.size === 0) return;
  
  const documentIds = Array.from(selectedDocuments.value);
  
  deletingDocumentId.value = "batch"; // 使用特殊值表示批量删除
  try {
    const result = await batchDeleteDocuments(documentIds);
    
    if (result.success_count > 0) {
      showToast("success", "批量删除成功", `成功删除 ${result.success_count} 个文档`);
      
      // 从列表中移除成功删除的文档
      result.success_ids.forEach(docId => {
        const docIndex = docs.value.findIndex(d => d.document_id === docId);
        if (docIndex >= 0) {
          docs.value.splice(docIndex, 1);
        }
        
        // 关闭相关的 WebSocket 连接
        const ws = activeWebSockets.get(docId);
        if (ws) {
          ws.close();
          activeWebSockets.delete(docId);
        }
      });
      
      // 显示失败的文档
      if (result.failed_count > 0) {
        const failedMessages = result.failed_ids.map(f => `${f.document_id}: ${f.reason}`).join("\n");
        showToast("error", "部分删除失败", `有 ${result.failed_count} 个文档删除失败`);
        console.error("删除失败的文档:", result.failed_ids);
      }
    } else {
      showToast("error", "批量删除失败", "没有文档被成功删除");
    }
    
    // 清空选择并退出选择模式
    selectedDocuments.value.clear();
    isSelectionMode.value = false;
    showDeleteDialog.value = false;
    isBatchDelete.value = false;
  } catch (error: any) {
    showToast("error", "批量删除失败", error.message || "请稍后重试");
  } finally {
    deletingDocumentId.value = null;
  }
};

const onFileChange = async (e: Event) => {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  // 立即添加到列表
  const tempDoc: Doc = {
    document_id: `temp-${Date.now()}`,
    title: file.name,
    lang_in: "en",
    lang_out: "zh",
    status: "uploading",
    progress: 0,
    thumbnailError: false,
  };
  docs.value.unshift(tempDoc);

  try {
    // 如果没有当前项目，创建新项目
    let project_id = currentProjectId.value;
    if (!project_id) {
      const projectRes = await createProject(projectName.value || "我的项目");
      project_id = projectRes.project_id;
      currentProjectId.value = project_id;
    }
    
    const res = await uploadPdf({ project_id, file, lang_in: LANG_IN_DEFAULT, lang_out: LANG_OUT_DEFAULT });
    
    // 更新文档ID（WebSocket 会发送真实进度）
    tempDoc.document_id = res.document_id;
    tempDoc.num_pages = res.num_pages;
    
    attachProgressWS(res.document_id, { projectId: project_id });
    
  } catch (error) {
    console.error("Upload failed:", error);
    docs.value = docs.value.filter((d) => d.document_id !== tempDoc.document_id);
  }
  
  input.value = "";
};

const onFilesChange = async (e: Event) => {
  const input = e.target as HTMLInputElement;
  const files = Array.from(input.files ?? []);
  if (files.length === 0) return;

  // 立即添加所有文件到列表
  const tempDocs: Doc[] = files.map((file, idx) => ({
    document_id: `temp-${Date.now()}-${idx}`,
    title: file.name,
    lang_in: LANG_IN_DEFAULT,
    lang_out: LANG_OUT_DEFAULT,
    status: "uploading" as DocStatus,
    progress: 0,
    thumbnailError: false,
  }));
  docs.value.unshift(...tempDocs);

  // 模拟批量上传进度
  const progressIntervals = tempDocs.map((doc) => {
    const timer = window.setInterval(() => {
      const idx = docs.value.findIndex(d => d.document_id === doc.document_id);
      if (idx >= 0) {
        const current = docs.value[idx];
        const next = Math.min(30, (current.progress || 0) + 2);
        docs.value.splice(idx, 1, { ...current, progress: next });
        if (next >= 30) {
          clearInterval(timer);
        }
      }
    }, 100);
    return timer;
  });

  try {
    const res = await batchUpload({ project_name: projectName.value || "批量项目", files, lang_in: LANG_IN_DEFAULT, lang_out: LANG_OUT_DEFAULT });
    
    // 设置当前项目ID
    if (res.project_id) {
      currentProjectId.value = res.project_id;
    }
    
    // 清除进度模拟
    progressIntervals.forEach(clearInterval);
    
    // 为每个文档创建 WebSocket 连接并更新状态（类似单个文件上传）
    res.documents?.forEach((d, idx) => {
      if (tempDocs[idx]) {
        const tempDoc = tempDocs[idx];
        tempDoc.document_id = d.document_id;
        tempDoc.status = "parsing";
        tempDoc.progress = 30; // 上传完成，开始解析
        
        // 创建 WebSocket 连接来跟踪进度（统一逻辑）
        attachProgressWS(d.document_id, { projectId: currentProjectId.value || undefined });
      }
    });
    
    // 不跳转到批次页面，保持在主页面显示所有文档
    // router.push(`/batch/${res.batch_id}`);
  } catch (error) {
    console.error("Batch upload failed:", error);
    progressIntervals.forEach(clearInterval);
    // 移除失败的文档
    tempDocs.forEach((doc) => {
      docs.value = docs.value.filter((d) => d.document_id !== doc.document_id);
    });
  }
  
  input.value = "";
};

const openDoc = (document_id: string) => {
  router.push(`/project/${document_id}`);
};

// Demo functionality removed - would cause 404 errors
// const openDemo = () => router.push("/project/demo");

const handlePendingUpload = async () => {
  const isUploading = route.query.uploading === "true";
  const filename = route.query.filename as string | undefined;
  
  if (!isUploading || !filename) return;
  
  // 检查是否有待上传的文件
  const pendingFile = (window as any).__pendingUploadFile as File | undefined;
  if (!pendingFile) {
    // 如果没有文件，清除参数
    router.replace('/app');
    return;
  }
  
  const decodedFilename = decodeURIComponent(filename);
  
  // 立即显示上传中的文档卡片
  const uploadingDoc: Doc = {
    document_id: `temp-${Date.now()}`,
    title: decodedFilename,
    lang_in: LANG_IN_DEFAULT,
    lang_out: LANG_OUT_DEFAULT,
    status: "uploading",
    progress: 0,
    thumbnailError: false,
  };
  docs.value.unshift(uploadingDoc);
  debugLog(`[上传] 创建文档卡片: ${uploadingDoc.document_id}, 初始进度: ${uploadingDoc.progress}%`);
  
  try {
    // 开始实际上传（使用当前项目ID，如果没有则创建新项目）
    let project_id = currentProjectId.value;
    if (!project_id) {
      const project = await createProject("我的项目");
      project_id = project.project_id;
      currentProjectId.value = project_id;
    }
    const res = await uploadPdf({ project_id, file: pendingFile, lang_in: LANG_IN_DEFAULT, lang_out: LANG_OUT_DEFAULT });
    
    // 更新文档ID（WebSocket 会发送真实进度）
    const docIndex = docs.value.findIndex(d => d.document_id === uploadingDoc.document_id);
    if (docIndex >= 0) {
      docs.value[docIndex] = {
        ...docs.value[docIndex],
        document_id: res.document_id,
        num_pages: res.num_pages,
      };
    }
    
    // 清除临时文件引用
    delete (window as any).__pendingUploadFile;
    
    // 更新 URL，添加 document_id
    router.replace({ query: { document_id: res.document_id, uploading: "true", filename } });
    
    attachProgressWS(res.document_id, { projectId: project_id });
    
  } catch (error) {
    console.error("Upload failed:", error);
    showToast("error", "上传失败", "请稍后重试");
    docs.value = docs.value.filter((d) => d.document_id !== uploadingDoc.document_id);
    router.replace('/app');
    delete (window as any).__pendingUploadFile;
  }
};

const loadDocumentFromQuery = async () => {
  const documentId = route.query.document_id as string | undefined;
  const isUploading = route.query.uploading === "true";
  const filename = route.query.filename as string | undefined;
  
  // 如果没有 document_id 但有 uploading 标记，说明是新的上传
  if (!documentId && isUploading) {
    await handlePendingUpload();
    return;
  }
  
  if (!documentId) return;

  // 检查是否已经存在
  const existingDoc = docs.value.find((d) => d.document_id === documentId);
  if (existingDoc && existingDoc.status === "ready") {
    // 如果已经就绪，清除查询参数即可
    router.replace({ query: {} });
    return;
  }

  // 如果文档不存在，创建临时文档（WebSocket 会发送初始状态）
  let doc = existingDoc || docs.value.find((d) => d.document_id === documentId);
  
  if (!doc) {
    // 创建临时文档，等待 WebSocket 发送初始状态
    doc = {
      document_id: documentId,
      title: filename ? decodeURIComponent(filename) : "处理中...",
      lang_in: LANG_IN_DEFAULT,
      lang_out: LANG_OUT_DEFAULT,
      status: isUploading ? "uploading" : "parsing",
      progress: isUploading ? 0 : 30,
      thumbnailError: false,
    };
    docs.value.unshift(doc);
  }

  // 使用 WebSocket 接收实时进度更新（统一逻辑）
  attachProgressWS(documentId, { projectId: currentProjectId.value || undefined });
  return;
};

onMounted(async () => {
  // 尝试从 URL 参数获取项目ID
  const projectIdFromQuery = route.query.project_id as string | undefined;
  
  if (projectIdFromQuery) {
    currentProjectId.value = projectIdFromQuery;
    await loadProjectDocuments(projectIdFromQuery);
  } else {
    // 优先加载用户的所有文档（不依赖项目）
    try {
      await loadUserDocuments(false);
      // 如果加载后没有文档，且没有当前项目ID，创建一个默认项目
      if (docs.value.length === 0 && !currentProjectId.value) {
        const { project_id } = await createProject(projectName.value || "我的项目");
        currentProjectId.value = project_id;
      }
    } catch (error) {
      console.error("加载用户文档失败:", error);
      // 如果加载失败，尝试创建或获取默认项目
      try {
        const { project_id } = await createProject(projectName.value || "我的项目");
        currentProjectId.value = project_id;
        await loadProjectDocuments(project_id);
      } catch (createError) {
        console.error("创建或加载项目失败:", createError);
      }
    }
  }
  
  await loadDocumentFromQuery();
  window.addEventListener("keydown", keyHandler);

  // 解析超时监控：定期检查解析耗时，超过阈值给出提示（每5秒检查一次）
  parsingMonitorTimer = window.setInterval(() => {
    const now = Date.now();
    docs.value.forEach((d) => {
      if (d.status === "parsing") {
        if (!parsingStartAt.has(d.document_id)) {
          parsingStartAt.set(d.document_id, now);
          return;
        }
        const started = parsingStartAt.get(d.document_id) || now;
        if (!parsingWarned.has(d.document_id) && now - started > PARSING_WARN_THRESHOLD_MS) {
          parsingWarned.add(d.document_id);
          showToast("warning", "解析耗时较长", "可点击“刷新状态”或稍后再查看进度");
        }
      }
    });
  }, 5000);

  // 尝试展示一次性安全向导
  maybeShowSecurityGuide();
});

onUnmounted(() => {
  // 清理所有 WebSocket 连接
  activeWebSockets.forEach((ws) => ws.disconnect());
  activeWebSockets.clear();
  window.removeEventListener("keydown", keyHandler);
  if (parsingMonitorTimer) {
    clearInterval(parsingMonitorTimer);
  }
});
</script>

<style scoped>
.dashboard {
  position: relative;
  min-height: calc(100vh - 200px);
}

.email-verification-banner {
  margin-bottom: 24px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border: 1px solid #f59e0b;
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.15);
}

.email-verification-content {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.email-verification-icon {
  width: 32px;
  height: 32px;
  color: #d97706;
  flex-shrink: 0;
}

.email-verification-icon svg {
  width: 100%;
  height: 100%;
}

.email-verification-text {
  flex: 1;
  min-width: 200px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.email-verification-text strong {
  font-size: 15px;
  font-weight: 600;
  color: #92400e;
}

.email-verification-text span {
  font-size: 14px;
  color: #78350f;
  line-height: 1.5;
}

.email-verification-actions {
  flex-shrink: 0;
}

.email-verification-btn {
  padding: 8px 16px;
  background: #f59e0b;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.email-verification-btn:hover:not(:disabled) {
  background: #d97706;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(245, 158, 11, 0.3);
}

.email-verification-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-spinner-small {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.empty-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 60px 32px;
}

.empty-state-content {
  text-align: center;
  max-width: 480px;
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.empty-state-icon {
  margin: 0 auto 24px;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.95) 0%, 
    rgba(250, 245, 255, 0.92) 25%,
    rgba(240, 249, 255, 0.92) 50%,
    rgba(255, 250, 240, 0.92) 75%,
    rgba(255, 255, 255, 0.95) 100%);
  border-radius: 24px;
  border: 1px solid rgba(226, 232, 240, 0.6);
  box-shadow: 
    0 8px 24px rgba(99, 102, 241, 0.08),
    0 4px 12px rgba(139, 92, 246, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.empty-state-title {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 12px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.empty-state-description {
  font-size: 15px;
  line-height: 1.6;
  color: #64748b;
  margin: 0;
  padding: 0 20px;
}

/* Dashboard 右上角“刷新列表” icon 按钮（UI/UX Pro：胶囊、柔和阴影、旋转动效） */
.dashboard-refresh-icon-btn {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  user-select: none;
  color: #334155;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.92));
  border: 1px solid rgba(226, 232, 240, 0.85);
  box-shadow:
    0 10px 22px rgba(15, 23, 42, 0.06),
    0 2px 6px rgba(15, 23, 42, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease, color 0.18s ease;
}

.dashboard-refresh-icon-btn svg {
  width: 18px;
  height: 18px;
}

.dashboard-refresh-icon-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(99, 102, 241, 0.35);
  color: #1e293b;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.10), rgba(59, 130, 246, 0.08));
  box-shadow:
    0 14px 28px rgba(99, 102, 241, 0.16),
    0 6px 12px rgba(59, 130, 246, 0.10),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.dashboard-refresh-icon-btn:active:not(:disabled) {
  transform: translateY(0px) scale(0.98);
}

.dashboard-refresh-icon-btn:disabled {
  cursor: not-allowed;
  color: #94a3b8;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.95), rgba(241, 245, 249, 0.92));
  border-color: rgba(226, 232, 240, 0.85);
  box-shadow:
    0 6px 14px rgba(15, 23, 42, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

@keyframes dashboardSpin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.dashboard-refresh-icon-btn.is-spinning svg {
  animation: dashboardSpin 0.8s linear infinite;
}

@media (max-width: 640px) {
  .empty-state {
    padding: 40px 24px;
  }

  .empty-state-icon {
    width: 100px;
    height: 100px;
    margin-bottom: 20px;
  }

  .empty-state-title {
    font-size: 20px;
  }

  .empty-state-description {
    font-size: 14px;
    padding: 0;
  }
}
</style>

