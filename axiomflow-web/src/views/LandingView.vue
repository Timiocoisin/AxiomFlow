<template>
  <section class="landing">
    <Snowflakes v-if="showSnowflakes" />
    <FloatingParticles v-if="showParticles" />
    <div class="landing-hero glass-card">
      <div class="hero-content">
        <img src="/icons/favicon.svg" alt="AxiomFlow" class="hero-icon" />
        <h1 class="hero-title">
          <span class="hero-title-main">{{ $t('landing.title') }}</span>
        </h1>
        <p class="hero-description">
          {{ $t('landing.description') }}
        </p>
        <div class="hero-features">
          <span 
            class="feature-tag" 
            :title="$t('landing.featureFormulaDesc')"
          >
            {{ $t('landing.featureFormula') }}
          </span>
          <span 
            class="feature-tag" 
            :title="$t('landing.featureLayoutDesc')"
          >
            {{ $t('landing.featureLayout') }}
          </span>
          <span 
            class="feature-tag" 
            :title="$t('landing.featureMultiLangDesc')"
          >
            {{ $t('landing.featureMultiLang') }}
          </span>
        </div>
        <p class="sr-only">
          {{ $t('landing.keyboardHint') }}
        </p>
        <div
          v-if="showFirstVisitHint"
          class="app-alert app-alert--info first-visit-hint"
          role="status"
          aria-live="polite"
        >
          <div class="app-alert-content">
            <p class="app-alert-title">
              {{ $t('landing.firstVisitHintTitle') }}
            </p>
            <p class="app-alert-message">
              {{ $t('landing.firstVisitHintBody') }}
            </p>
          </div>
          <button
            type="button"
            class="app-alert-close"
            @click="dismissFirstVisitHint"
          >
            {{ $t('landing.firstVisitHintClose') }}
          </button>
        </div>
        <button
          v-if="showFirstVisitBadge"
          type="button"
          class="first-visit-hint-badge"
          @click="openFirstVisitHintFromBadge"
        >
          <span aria-hidden="true">💡</span>
          <span>{{ $t('landing.firstVisitHintTitle') }}</span>
        </button>
      </div>
      <!-- 首次访问提示气泡 -->
      <div
        v-if="showFirstUseBubble"
        class="first-use-bubble"
        role="tooltip"
        aria-live="polite"
      >
        {{ $t('landing.firstUseHint') }}
      </div>
      <!-- 屏幕阅读器提示区域 -->
      <div 
        id="landing-aria-live" 
        class="sr-only" 
        role="status" 
        aria-live="polite" 
        aria-atomic="true"
      >
        {{ ariaLiveMessage }}
      </div>
      <div
        class="upload-dropzone"
        ref="uploadDropzone"
        :class="{ 
          'upload-dropzone--dragover': isDragging,
          'upload-dropzone--uploading': isUploading
        }"
        role="button"
        tabindex="0"
        :aria-label="$t('landing.uploadAreaLabel') || 'Upload PDF file'"
        :aria-busy="isUploading"
        :aria-describedby="uploadError ? 'upload-error' : 'upload-hints'"
        @click="pickFile"
        @keydown.enter="pickFile"
        @keydown.space.prevent="pickFile"
        @dragover.prevent="handleDragOver"
        @dragleave.prevent="handleDragLeave"
        @drop.prevent="handleDrop"
        @touchstart.prevent="handleTouchStart"
        @touchend.prevent="handleTouchEnd"
        @touchmove.prevent="handleTouchMove"
      >
        <div class="upload-content">
          <!-- 首次加载 Skeleton 覆盖层（不影响实际内容渲染） -->
          <div v-if="showSkeleton" class="upload-skeleton" aria-hidden="true"></div>
          <!-- 上传中状态 -->
          <div v-if="isUploading" class="upload-status">
            <div class="upload-spinner" aria-hidden="true"></div>
            <span class="upload-status-text">{{ $t('landing.uploading') || 'Uploading...' }}</span>
          </div>
          <!-- 拖拽时显示文件名预览 -->
          <div v-else-if="isDragging && draggedFileName" class="upload-drag-preview">
            <svg class="upload-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M14 2V8H20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <div class="upload-text">
              <span class="upload-text-primary">{{ $t('landing.dragFileDetected', { filename: draggedFileName }) }}</span>
            </div>
          </div>
          <!-- 文件验证反馈 -->
          <div v-else-if="detectedFile" class="upload-file-detected">
            <svg class="upload-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M14 2V8H20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M9 12L11 14L15 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <div class="upload-text">
              <span class="upload-text-primary">{{ $t('landing.fileDetected', { filename: detectedFile.name, size: formatFileSize(detectedFile.size) }) }}</span>
            </div>
          </div>
          <!-- 默认状态 -->
          <div v-else class="upload-placeholder">
            <svg class="upload-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <path d="M12 15V3M12 3L8 7M12 3L16 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 17L2 19C2 20.1046 2.89543 21 4 21L20 21C21.1046 21 22 20.1046 22 19L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <div class="upload-text">
              <span class="upload-text-primary">{{ $t('landing.dragPdf') }}</span>
              <span v-if="isTouchDevice" class="upload-text-mobile-hint">{{ $t('landing.clickToUpload') }}</span>
            </div>
          </div>
        </div>
        <p
          v-if="isDragging && !isUploading && !uploadError && !draggedFileName"
          class="upload-drag-hint"
        >
          {{ $t('landing.dragHint') }}
        </p>
        <!-- 上传跳转前的过渡提示 -->
        <div
          v-if="isPreparingWorkspace"
          class="upload-preparing-workspace"
          role="status"
          aria-live="polite"
        >
          {{ $t('landing.preparingWorkspace') }}
        </div>
      </div>
      <!-- 文件验证提示 -->
      <div class="upload-hints" id="upload-hints" role="note">
        <span class="upload-hint">
          {{ $t('landing.fileTypeHint') || 'Only PDF files are supported' }}
        </span>
        <span class="upload-hint">
          {{ $t('landing.fileSizeHint') || 'Maximum file size: 50MB' }}
        </span>
        <button
          type="button"
          class="upload-hints-toggle"
          @click="showAllHints = !showAllHints"
          :aria-expanded="showAllHints"
        >
          {{ showAllHints ? ($t('landing.lessHints') || 'Less') : ($t('landing.moreHints') || 'More details') }}
        </button>
        <div v-if="showAllHints" class="upload-hints-extra">
          <span class="upload-hint">
            {{ $t('landing.loginRequiredHint') }}
          </span>
          <span class="upload-hint">
            {{ $t('landing.privacyHint') }}
          </span>
          <span class="upload-help-fixed">
            {{ $t('landing.helpFixedHint') }}
          </span>
        </div>
      </div>
      <!-- 底部错误 / 帮助提示条 -->
      <div
        v-if="uploadError"
        class="landing-help-bottom-bar landing-help-bottom-bar--error"
        role="alert"
        id="upload-error"
        aria-live="assertive"
      >
        <div class="landing-help-bottom-bar-main">
          <span class="landing-help-bottom-bar-icon" aria-hidden="true">!</span>
          <div class="landing-help-bottom-bar-text">
            <div class="landing-help-bottom-bar-title">
              {{ uploadError }}
            </div>
            <div
              v-if="errorType === 'fileType'"
              class="landing-help-bottom-bar-sub"
            >
              {{ $t('landing.errorFileTypeHelp') }}
            </div>
            <div
              v-else-if="errorType === 'fileTooLarge'"
              class="landing-help-bottom-bar-sub"
            >
              {{ $t('landing.errorFileTooLargeHelp') }}
            </div>
          </div>
        </div>
        <div class="landing-help-bottom-bar-actions">
          <button
            type="button"
            class="landing-help-bottom-bar-btn landing-help-bottom-bar-btn--primary"
            @click="pickFile"
          >
            {{ $t('landing.retryUpload') }}
          </button>
          <button
            type="button"
            class="landing-help-bottom-bar-btn"
            @click="goToHelp"
          >
            {{ $t('landing.errorHelpLink') }}
          </button>
          <button
            type="button"
            class="landing-help-bottom-bar-close"
            @click="clearError"
            :aria-label="$t('landing.dismissError') || 'Dismiss error'"
          >
            ×
          </button>
        </div>
      </div>
      <!-- 首页长时间无操作时的轻量帮助条 -->
      <div
        v-else-if="showIdleHelpBar"
        class="landing-help-bottom-bar landing-help-bottom-bar--idle"
        role="status"
        aria-live="polite"
      >
        <div class="landing-help-bottom-bar-main">
          <span class="landing-help-bottom-bar-icon" aria-hidden="true">?</span>
          <div class="landing-help-bottom-bar-text">
            <div class="landing-help-bottom-bar-title">
              {{ $t('landing.idleHelpText') }}
            </div>
          </div>
        </div>
        <div class="landing-help-bottom-bar-actions">
          <button
            type="button"
            class="landing-help-bottom-bar-btn landing-help-bottom-bar-btn--primary"
            @click="handleIdleHelpClick"
          >
            {{ $t('landing.idleHelpAction') }}
          </button>
          <button
            type="button"
            class="landing-help-bottom-bar-close"
            @click="showIdleHelpBar = false"
            :aria-label="$t('landing.dismissIdleHelp') || 'Dismiss help'"
          >
            ×
          </button>
        </div>
      </div>
      <input 
        ref="fileInput" 
        type="file" 
        accept="application/pdf" 
        style="display: none" 
        @change="handleFileSelect"
        :aria-label="$t('landing.fileInputLabel') || 'Select PDF file'"
      />
      <!-- 文件预览模态框 -->
      <div v-if="previewFile && previewUrl" class="file-preview-modal file-preview-modal--overlay" @click.self="closePreview">
        <div class="file-preview-content" role="dialog" aria-modal="true" aria-labelledby="preview-title">
          <div class="file-preview-header">
            <h3 id="preview-title" class="file-preview-title">{{ previewFile.name }}</h3>
            <button 
              class="file-preview-close" 
              @click="closePreview"
              ref="previewCloseButton"
              :aria-label="$t('landing.closePreview') || 'Close preview'"
            >
              ×
            </button>
          </div>
          <div class="file-preview-body">
            <!-- 预览加载状态 -->
            <div v-if="isPreviewLoading" class="file-preview-loading">
              <div class="file-preview-loading-spinner" aria-hidden="true"></div>
              <span class="file-preview-loading-text">{{ $t('landing.previewLoading') }}</span>
            </div>
            <iframe 
              v-show="!isPreviewLoading"
              :src="previewUrl" 
              class="file-preview-iframe"
              title="PDF Preview"
              @load="handlePreviewLoad"
            ></iframe>
          </div>
          <div class="file-preview-footer">
            <button class="file-preview-btn file-preview-btn--secondary" @click="closePreview">
              {{ $t('landing.cancel') || 'Cancel' }}
            </button>
            <button class="file-preview-btn file-preview-btn--primary" @click="uploadFile(previewFile!)">
              {{ $t('landing.confirmUpload') || 'Confirm Upload' }}
            </button>
          </div>
        </div>
      </div>
      <!-- 可信背书与隐私说明 -->
      <section
        class="landing-trust-section"
        :aria-label="$t('landing.trustTitle')"
      >
        <div class="landing-trust-main">
          <h2 class="landing-trust-title">
            {{ $t('landing.trustTitle') }}
          </h2>
          <p class="landing-trust-subtitle">
            {{ $t('landing.trustSubtitle') }}
          </p>
          <div class="landing-trust-tags">
            <span class="landing-trust-tag">
              {{ $t('landing.trustUseCaseResearch') }}
            </span>
            <span class="landing-trust-tag">
              {{ $t('landing.trustUseCaseTeaching') }}
            </span>
            <span class="landing-trust-tag">
              {{ $t('landing.trustUseCasePublishing') }}
            </span>
            <span class="landing-trust-tag">
              {{ $t('landing.trustUseCaseIndustry') }}
            </span>
          </div>
        </div>
        <button
          type="button"
          class="landing-privacy-entry"
          @click="openPrivacyModal"
        >
          {{ $t('landing.privacyLinkLabel') }}
        </button>
      </section>
      <!-- 隐私与安全弹窗 -->
      <div
        v-if="showPrivacyModal"
        class="landing-privacy-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="landing-privacy-title"
      >
        <div
          class="landing-privacy-modal-backdrop"
          @click="closePrivacyModal"
        ></div>
        <div class="landing-privacy-modal-content">
          <h2 id="landing-privacy-title" class="landing-privacy-modal-title">
            {{ $t('landing.privacyModalTitle') }}
          </h2>
          <p class="landing-privacy-modal-desc">
            {{ $t('landing.privacyModalDesc') }}
          </p>
          <ul class="landing-privacy-modal-list">
            <li>
              {{ $t('landing.privacyModalItemRetention') }}
            </li>
            <li>
              {{ $t('landing.privacyModalItemTraining') }}
            </li>
            <li>
              {{ $t('landing.privacyModalItemDeletion') }}
            </li>
          </ul>
          <div class="landing-privacy-modal-actions">
            <button
              type="button"
              class="landing-privacy-modal-link"
              @click="goToHelpFromPrivacy"
            >
              {{ $t('landing.privacyModalAction') }}
            </button>
            <button
              type="button"
              class="landing-privacy-modal-close"
              @click="closePrivacyModal"
            >
              {{ $t('landing.privacyModalClose') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, onUnmounted, nextTick, onMounted, defineAsyncComponent } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { useUserStore } from "@/stores/user";
import { createProject, uploadPdf } from "@/lib/api";

const Snowflakes = defineAsyncComponent(() => import("@/components/Snowflakes.vue"));
const FloatingParticles = defineAsyncComponent(() => import("@/components/FloatingParticles.vue"));

const router = useRouter();
const { t } = useI18n();
const userStore = useUserStore();

const fileInput = ref<HTMLInputElement | null>(null);
const uploadDropzone = ref<HTMLElement | null>(null);
const isDragging = ref(false);
const isUploading = ref(false);
const uploadError = ref<string | null>(null);
const errorType = ref<'fileType' | 'fileTooLarge' | 'fileEmpty' | null>(null);
const previewFile = ref<File | null>(null);
const previewUrl = ref<string | null>(null);
const previewCloseButton = ref<HTMLButtonElement | null>(null);
const isPreviewLoading = ref(true);
const draggedFileName = ref<string | null>(null);
const detectedFile = ref<File | null>(null);
const isPreparingWorkspace = ref(false);
const ariaLiveMessage = ref('');

const showSnowflakes = ref(true);
const showParticles = ref(true);

const FIRST_VISIT_HINT_KEY = "landing_first_visit_v1";
const FIRST_USE_BUBBLE_KEY = "landing_first_use_bubble_v1";
const IDLE_HELP_KEY = "landing_idle_help_date_v1";
const showFirstVisitHint = ref(false);
const showFirstVisitBadge = ref(false);
const showFirstUseBubble = ref(false);
const showAllHints = ref(false);
const showIdleHelpBar = ref(false);
const showSkeleton = ref(true);
const showPrivacyModal = ref(false);
let idleTimer: number | undefined;

// 文件大小限制：50MB
const MAX_FILE_SIZE = 50 * 1024 * 1024;

// 触摸设备检测
const isTouchDevice = ref(false);
if (typeof window !== 'undefined') {
  isTouchDevice.value = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
}

// 简单埋点钩子，后续可替换为真实埋点上报
const trackLandingEvent = (event: string, payload?: Record<string, any>) => {
  try {
    if (import.meta.env.DEV) {
      // 开发环境在控制台打印，便于观察
      // eslint-disable-next-line no-console
      console.debug("[landing]", event, payload || {});
    }
    // 未来可在此调用实际埋点 SDK
  } catch {
    // 忽略埋点异常，避免影响主流程
  }
};

// 根据设备和用户偏好决定是否显示动效 & 首次访问提示
onMounted(() => {
  if (typeof window === 'undefined') return;
  const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const isSmallScreen = window.innerWidth < 768;
  // 小屏或减少动效偏好时，关闭大部分背景动效
  if (prefersReducedMotion || isSmallScreen) {
    showSnowflakes.value = false;
    showParticles.value = false;
  }
  // 首次访问轻量提示：仅在未标记过的情况下展示一次
  try {
    const seen = window.localStorage.getItem(FIRST_VISIT_HINT_KEY);
    if (!seen) {
      showFirstVisitHint.value = true;
      trackLandingEvent("first_visit_hint_shown");
      // 停留一段时间后自动收起为小角标
      setTimeout(() => {
        if (showFirstVisitHint.value) {
          showFirstVisitHint.value = false;
          showFirstVisitBadge.value = true;
          trackLandingEvent("first_visit_hint_auto_collapsed");
        }
      }, 10000);
      // 向下滚动一定距离也收起为角标
      const onScroll = () => {
        if (!showFirstVisitHint.value) return;
        if (window.scrollY > 160) {
          showFirstVisitHint.value = false;
          showFirstVisitBadge.value = true;
          trackLandingEvent("first_visit_hint_collapsed_on_scroll");
        }
      };
      window.addEventListener("scroll", onScroll, { passive: true });
      // 组件卸载时移除监听
      onUnmounted(() => {
        if (typeof window !== "undefined") {
          window.removeEventListener("scroll", onScroll);
        }
      });
    }
    // 首次访问提示气泡
    const bubbleSeen = window.localStorage.getItem(FIRST_USE_BUBBLE_KEY);
    if (!bubbleSeen && userStore.isLoggedIn) {
      showFirstUseBubble.value = true;
      setTimeout(() => {
        showFirstUseBubble.value = false;
        try {
          window.localStorage.setItem(FIRST_USE_BUBBLE_KEY, "1");
        } catch {
          // ignore
        }
      }, 3000);
    }
  } catch {
    // ignore
  }
});

// 首屏 Skeleton 与首页闲置帮助条（每天最多出现一次）
onMounted(() => {
  if (typeof window === 'undefined') return;

  // 轻量 Skeleton，缓解首载空白感
  setTimeout(() => {
    showSkeleton.value = false;
  }, 400);

  const resetIdleTimer = () => {
    if (typeof window === 'undefined') return;
    showIdleHelpBar.value = false;
    const today = new Date().toISOString().slice(0, 10);
    const stored = window.localStorage.getItem(IDLE_HELP_KEY);
    if (stored === today) {
      return;
    }
    if (idleTimer) {
      window.clearTimeout(idleTimer);
    }
    idleTimer = window.setTimeout(() => {
      showIdleHelpBar.value = true;
      try {
        window.localStorage.setItem(IDLE_HELP_KEY, today);
      } catch {
        // ignore
      }
    }, 20000);
  };

  resetIdleTimer();

  const events: (keyof WindowEventMap)[] = ["click", "keydown", "scroll"];
  const handleInteraction = () => resetIdleTimer();
  events.forEach((evt) => {
    window.addEventListener(evt, handleInteraction, { passive: true });
  });

  onUnmounted(() => {
    if (typeof window !== "undefined") {
      events.forEach((evt) => {
        window.removeEventListener(evt, handleInteraction);
      });
      if (idleTimer) {
        window.clearTimeout(idleTimer);
      }
    }
  });
});

const dismissFirstVisitHint = () => {
  showFirstVisitHint.value = false;
  showFirstVisitBadge.value = false;
  try {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(FIRST_VISIT_HINT_KEY, "1");
    }
  } catch {
    // ignore
  }
  trackLandingEvent("first_visit_hint_dismissed");
};

const openFirstVisitHintFromBadge = () => {
  showFirstVisitHint.value = true;
  showFirstVisitBadge.value = false;
  trackLandingEvent("first_visit_hint_badge_clicked");
};

const pickFile = () => {
  if (!userStore.isLoggedIn) {
    router.push(`/auth?redirect=${encodeURIComponent("/")}`);
    return;
  }
  fileInput.value?.click();
};

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

const handleDragOver = (e: DragEvent) => {
  if (!userStore.isLoggedIn) {
    e.preventDefault();
    return;
  }
  isDragging.value = true;
  e.dataTransfer!.dropEffect = "copy";
  
  // 检测拖拽的文件名
  const files = Array.from(e.dataTransfer?.items || []);
  const pdfItem = files.find((item) => {
    if (item.kind === 'file') {
      const file = item.getAsFile();
      return file && file.name.toLowerCase().endsWith('.pdf');
    }
    return false;
  });
  if (pdfItem) {
    const file = pdfItem.getAsFile();
    if (file) {
      draggedFileName.value = file.name;
    }
  } else {
    draggedFileName.value = null;
  }
  
  trackLandingEvent("drag_over_upload_area");
};

const handleDragLeave = () => {
  isDragging.value = false;
  draggedFileName.value = null;
};

const handleDrop = async (e: DragEvent) => {
  isDragging.value = false;
  const droppedFileName = draggedFileName.value;
  draggedFileName.value = null;
  clearError();
  
  if (!userStore.isLoggedIn) {
    e.preventDefault();
    router.push(`/auth?redirect=${encodeURIComponent("/")}`);
    return;
  }
  
  const files = Array.from(e.dataTransfer?.files || []);
  const pdfFile = files.find((f) => f.name.toLowerCase().endsWith(".pdf"));
  
  if (pdfFile) {
    trackLandingEvent("drop_pdf_file", { name: pdfFile.name, size: pdfFile.size });
    // 显示文件验证反馈
    detectedFile.value = pdfFile;
    setTimeout(() => {
      validateAndUploadFile(pdfFile);
    }, 300);
  } else {
    setError(t('landing.uploadPdfOnly') || 'Please upload a PDF file only', 'fileType');
  }
};

const handleFileSelect = (e: Event) => {
  if (!userStore.isLoggedIn) {
    router.push(`/auth?redirect=${encodeURIComponent("/")}`);
    return;
  }
  
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (file) {
    // 立即显示文件验证反馈
    detectedFile.value = file;
    trackLandingEvent("select_file", { name: file.name, size: file.size });
    
    // 短暂延迟后验证，让用户看到文件已被识别
    setTimeout(() => {
      if (file.name.toLowerCase().endsWith(".pdf")) {
        trackLandingEvent("select_pdf_file", { name: file.name, size: file.size });
        validateAndUploadFile(file);
      } else {
        detectedFile.value = null;
        setError(t('landing.uploadPdfOnly') || 'Please upload a PDF file only', 'fileType');
      }
    }, 300);
  }
  input.value = "";
};

const validateAndUploadFile = (file: File) => {
  clearError();
  detectedFile.value = null;
  
  // 验证文件类型
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    setError(t('landing.uploadPdfOnly') || 'Please upload a PDF file only', 'fileType');
    return;
  }
  
  // 验证文件大小
  if (file.size > MAX_FILE_SIZE) {
    const maxSizeMB = MAX_FILE_SIZE / (1024 * 1024);
    setError(t('landing.fileTooLarge', { maxSizeMB }) || `File size exceeds ${maxSizeMB}MB limit`, 'fileTooLarge');
    return;
  }
  
  // 验证文件是否为空
  if (file.size === 0) {
    setError(t('landing.fileEmpty') || 'The selected file is empty', 'fileEmpty');
    return;
  }
  
  // 显示预览（低优先级功能）
  showPreview(file);
};

const setError = (message: string, type: 'fileType' | 'fileTooLarge' | 'fileEmpty' | null = null) => {
  uploadError.value = message;
  errorType.value = type;
  isUploading.value = false;
  detectedFile.value = null;
  // 5秒后自动清除错误
  setTimeout(() => {
    if (uploadError.value === message) {
      clearError();
    }
  }, 5000);
};

const clearError = () => {
  uploadError.value = null;
  errorType.value = null;
};

const goToHelp = () => {
  router.push({ path: "/settings", query: { tab: "help" } });
};

const handleIdleHelpClick = () => {
  showIdleHelpBar.value = false;
  goToHelp();
};

// 触摸事件处理（移动端优化）
let touchStartY = 0;
let touchStartTime = 0;

const handleTouchStart = (e: TouchEvent) => {
  if (!userStore.isLoggedIn) return;
  touchStartY = e.touches[0].clientY;
  touchStartTime = Date.now();
  // 轻微视觉反馈
  if (e.currentTarget) {
    (e.currentTarget as HTMLElement).classList.add('upload-dropzone--touch-active');
  }
};

const handleTouchMove = (e: TouchEvent) => {
  if (!userStore.isLoggedIn) return;
  // 防止滚动
  e.preventDefault();
};

const handleTouchEnd = (e: TouchEvent) => {
  if (!userStore.isLoggedIn) return;
  const touchEndY = e.changedTouches[0].clientY;
  const touchEndTime = Date.now();
  const deltaY = Math.abs(touchEndY - touchStartY);
  const deltaTime = touchEndTime - touchStartTime;
  
  // 移除触摸激活状态
  if (e.currentTarget) {
    (e.currentTarget as HTMLElement).classList.remove('upload-dropzone--touch-active');
  }
  
  // 如果是快速轻触（小于200ms且移动距离小于10px），触发文件选择
  if (deltaTime < 200 && deltaY < 10) {
    pickFile();
  }
};

// 文件预览功能
const showPreview = (file: File) => {
  // 清理之前的预览
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
  }
  
  previewFile.value = file;
  previewUrl.value = URL.createObjectURL(file);
  isPreviewLoading.value = true;
  // 锁定背景滚动并聚焦关闭按钮
  if (typeof document !== "undefined") {
    document.body.classList.add("modal-open");
  }
  nextTick(() => {
    previewCloseButton.value?.focus();
  });
};

const handlePreviewLoad = () => {
  isPreviewLoading.value = false;
};

const closePreview = () => {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
  }
  previewFile.value = null;
  previewUrl.value = null;
  // 解锁背景滚动并将焦点还原到上传区域
  if (typeof document !== "undefined") {
    document.body.classList.remove("modal-open");
  }
  nextTick(() => {
    uploadDropzone.value?.focus();
  });
};

const openPrivacyModal = () => {
  showPrivacyModal.value = true;
  if (typeof document !== "undefined") {
    document.body.classList.add("modal-open");
  }
};

const closePrivacyModal = () => {
  showPrivacyModal.value = false;
  if (typeof document !== "undefined") {
    document.body.classList.remove("modal-open");
  }
};

const goToHelpFromPrivacy = () => {
  closePrivacyModal();
  goToHelp();
};

const uploadFile = (file: File) => {
  clearError();
  isUploading.value = true;
  detectedFile.value = null;
  
  // 清理预览
  closePreview();
  
  // 显示过渡提示
  isPreparingWorkspace.value = true;
  ariaLiveMessage.value = t('landing.uploadingToWorkspace') || 'Redirecting to workspace, file is ready';
  
  // 短暂显示上传状态，然后跳转
  setTimeout(() => {
    const fileName = encodeURIComponent(file.name);
    router.push(`/app?uploading=true&filename=${fileName}`);
    
    // 将文件对象存储到全局变量（通过 window 对象），供文档页面使用
    (window as any).__pendingUploadFile = file;
  }, 300);
};

// 清理预览 URL（组件卸载时）
onUnmounted(() => {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
  }
  if (typeof document !== "undefined") {
    document.body.classList.remove("modal-open");
  }
});
</script>

