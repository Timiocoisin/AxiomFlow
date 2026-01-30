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
          'upload-dropzone--dragover': isDragging
        }"
        @click="pickFile"
        @dragover.prevent="handleDragOver"
        @dragleave.prevent="handleDragLeave"
        @drop.prevent="handleDrop"
      >
        <div class="upload-content">
          <div class="upload-placeholder">
            <svg class="upload-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
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
      <input ref="fileInput" type="file" accept="application/pdf" style="display: none" @change="handleFileSelect" />
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
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
  
  if (!userStore.isLoggedIn) {
    e.preventDefault();
    router.push(`/auth?redirect=${encodeURIComponent("/")}`);
    return;
  }
  
  const files = Array.from(e.dataTransfer?.files || []);
  const pdfFile = files.find((f) => f.name.toLowerCase().endsWith(".pdf"));
  
  if (pdfFile) {
    uploadFile(pdfFile);
  } else {
    alert(t('landing.uploadPdfOnly'));
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
    uploadFile(file);
  }
  input.value = "";
};

const uploadFile = (file: File) => {
  // 立即跳转到文档页面，不显示上传状态
  const fileName = encodeURIComponent(file.name);
  router.push(`/app?uploading=true&filename=${fileName}`);
  
  // 将文件对象存储到全局变量（通过 window 对象），供文档页面使用
  (window as any).__pendingUploadFile = file;
};
</script>


