<template>
  <section class="landing">
    <Snowflakes />
    <FloatingParticles />
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
          <span class="feature-tag">{{ $t('landing.featureFormula') }}</span>
          <span class="feature-tag">{{ $t('landing.featureLayout') }}</span>
          <span class="feature-tag">{{ $t('landing.featureMultiLang') }}</span>
        </div>
      </div>
      <div
        class="upload-dropzone"
        :class="{ 
          'upload-dropzone--dragover': isDragging,
          'upload-dropzone--uploading': isUploading,
          'upload-dropzone--error': uploadError
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
          <!-- 上传中状态 -->
          <div v-if="isUploading" class="upload-status">
            <div class="upload-spinner" aria-hidden="true"></div>
            <span class="upload-status-text">{{ $t('landing.uploading') || 'Uploading...' }}</span>
          </div>
          <!-- 错误状态 -->
          <div v-else-if="uploadError" class="upload-error" id="upload-error" role="alert">
            <svg class="upload-error-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="M12 8V12M12 16H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <span class="upload-error-text">{{ uploadError }}</span>
            <button 
              class="upload-error-dismiss" 
              @click.stop="clearError"
              :aria-label="$t('landing.dismissError') || 'Dismiss error'"
            >
              ×
            </button>
          </div>
          <!-- 默认状态 -->
          <div v-else class="upload-placeholder">
            <svg class="upload-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <path d="M12 15V3M12 3L8 7M12 3L16 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 17L2 19C2 20.1046 2.89543 21 4 21L20 21C21.1046 21 22 20.1046 22 19L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <div class="upload-text">
              <span class="upload-text-primary">{{ $t('landing.dragPdf') }}</span>
              <span class="upload-text-secondary">{{ $t('landing.orClick') }}</span>
            </div>
          </div>
        </div>
      </div>
      <!-- 文件验证提示 -->
      <div class="upload-hints" id="upload-hints" role="note">
        <span class="upload-hint">{{ $t('landing.fileTypeHint') || 'Only PDF files are supported' }}</span>
        <span class="upload-hint">{{ $t('landing.fileSizeHint') || 'Maximum file size: 50MB' }}</span>
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
              :aria-label="$t('landing.closePreview') || 'Close preview'"
            >
              ×
            </button>
          </div>
          <div class="file-preview-body">
            <iframe 
              :src="previewUrl" 
              class="file-preview-iframe"
              title="PDF Preview"
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
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { useUserStore } from "@/stores/user";
import { createProject, uploadPdf } from "@/lib/api";
import Snowflakes from "@/components/Snowflakes.vue";
import FloatingParticles from "@/components/FloatingParticles.vue";

const router = useRouter();
const { t } = useI18n();
const userStore = useUserStore();

const fileInput = ref<HTMLInputElement | null>(null);
const isDragging = ref(false);
const isUploading = ref(false);
const uploadError = ref<string | null>(null);
const previewFile = ref<File | null>(null);
const previewUrl = ref<string | null>(null);

// 文件大小限制：50MB
const MAX_FILE_SIZE = 50 * 1024 * 1024;

// 触摸设备检测
const isTouchDevice = ref(false);
if (typeof window !== 'undefined') {
  isTouchDevice.value = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
}

const pickFile = () => {
  if (!userStore.isLoggedIn) {
    router.push(`/auth?redirect=${encodeURIComponent("/")}`);
    return;
  }
  fileInput.value?.click();
};

const handleDragOver = (e: DragEvent) => {
  if (!userStore.isLoggedIn) {
    e.preventDefault();
    return;
  }
  isDragging.value = true;
  e.dataTransfer!.dropEffect = "copy";
};

const handleDragLeave = () => {
  isDragging.value = false;
};

const handleDrop = async (e: DragEvent) => {
  isDragging.value = false;
  clearError();
  
  if (!userStore.isLoggedIn) {
    e.preventDefault();
    router.push(`/auth?redirect=${encodeURIComponent("/")}`);
    return;
  }
  
  const files = Array.from(e.dataTransfer?.files || []);
  const pdfFile = files.find((f) => f.name.toLowerCase().endsWith(".pdf"));
  
  if (pdfFile) {
    validateAndUploadFile(pdfFile);
  } else {
    setError(t('landing.uploadPdfOnly') || 'Please upload a PDF file only');
  }
};

const handleFileSelect = (e: Event) => {
  if (!userStore.isLoggedIn) {
    router.push(`/auth?redirect=${encodeURIComponent("/")}`);
    return;
  }
  
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (file && file.name.toLowerCase().endsWith(".pdf")) {
    validateAndUploadFile(file);
  } else if (file) {
    setError(t('landing.uploadPdfOnly') || 'Please upload a PDF file only');
  }
  input.value = "";
};

const validateAndUploadFile = (file: File) => {
  clearError();
  
  // 验证文件类型
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    setError(t('landing.uploadPdfOnly') || 'Please upload a PDF file only');
    return;
  }
  
  // 验证文件大小
  if (file.size > MAX_FILE_SIZE) {
    const maxSizeMB = MAX_FILE_SIZE / (1024 * 1024);
    setError(t('landing.fileTooLarge', { maxSizeMB }) || `File size exceeds ${maxSizeMB}MB limit`);
    return;
  }
  
  // 验证文件是否为空
  if (file.size === 0) {
    setError(t('landing.fileEmpty') || 'The selected file is empty');
    return;
  }
  
  // 显示预览（低优先级功能）
  showPreview(file);
};

const setError = (message: string) => {
  uploadError.value = message;
  isUploading.value = false;
  // 5秒后自动清除错误
  setTimeout(() => {
    if (uploadError.value === message) {
      clearError();
    }
  }, 5000);
};

const clearError = () => {
  uploadError.value = null;
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
};

const closePreview = () => {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
  }
  previewFile.value = null;
  previewUrl.value = null;
};

const uploadFile = (file: File) => {
  clearError();
  isUploading.value = true;
  
  // 清理预览
  closePreview();
  
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
});
</script>


