<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="visible"
        class="modal-overlay confirm-dialog-overlay"
        @click.self="handleCancel"
        role="dialog"
        aria-labelledby="confirm-dialog-title"
        aria-modal="true"
      >
        <div class="modal-content confirm-dialog-content">
          <!-- 图标 -->
          <div class="confirm-dialog-icon" :class="`confirm-dialog-icon--${type}`">
            <svg v-if="type === 'danger'" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 9V13M12 17H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <svg v-else-if="type === 'warning'" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 9V13M12 17H12.01M10.29 3.86L1.82 18C1.64537 18.3024 1.55299 18.6453 1.55201 18.9945C1.55103 19.3437 1.64151 19.6871 1.81445 19.9905C1.98738 20.2939 2.23675 20.5467 2.53773 20.7238C2.83871 20.9009 3.18082 20.9962 3.53 21H20.47C20.8192 20.9962 21.1613 20.9009 21.4623 20.7238C21.7633 20.5467 22.0126 20.2939 22.1856 19.9905C22.3585 19.6871 22.449 19.3437 22.448 18.9945C22.447 18.6453 22.3546 18.3024 22.18 18L13.71 3.86C13.5322 3.56611 13.2807 3.32312 12.9812 3.15447C12.6817 2.98583 12.3438 2.89725 12 2.89725C11.6562 2.89725 11.3183 2.98583 11.0188 3.15447C10.7193 3.32312 10.4678 3.56611 10.29 3.86Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M13 16H12V12H11M12 8H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          
          <!-- 标题 -->
          <h2 id="confirm-dialog-title" class="confirm-dialog-title">{{ title }}</h2>
          
          <!-- 内容 -->
          <p v-if="message" class="confirm-dialog-message">{{ message }}</p>
          
          <!-- 按钮组 -->
          <div class="confirm-dialog-actions">
            <button
              class="confirm-dialog-button confirm-dialog-button--cancel"
              @click="handleCancel"
              :disabled="loading"
            >
              {{ cancelTextComputed }}
            </button>
            <button
              class="confirm-dialog-button confirm-dialog-button--confirm"
              :class="`confirm-dialog-button--${type}`"
              @click="handleConfirm"
              :disabled="loading"
            >
              {{ confirmTextComputed }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, watch } from "vue";
import { useI18n } from "vue-i18n";

export interface ConfirmDialogProps {
  visible: boolean;
  title: string;
  message?: string;
  type?: "danger" | "warning" | "info";
  confirmText?: string;
  cancelText?: string;
  loading?: boolean;
}

const props = withDefaults(defineProps<ConfirmDialogProps>(), {
  type: "danger",
  loading: false,
});

const { t } = useI18n();
const confirmTextComputed = computed(() => props.confirmText || t("common.confirm"));
const cancelTextComputed = computed(() => props.cancelText || t("common.cancel"));

const emit = defineEmits<{
  confirm: [];
  cancel: [];
  "update:visible": [value: boolean];
}>();

const handleConfirm = () => {
  if (!props.loading) {
    emit("confirm");
  }
};

const handleCancel = () => {
  if (!props.loading) {
    emit("cancel");
    emit("update:visible", false);
  }
};

// 监听 visible 变化，处理 ESC 键
let escHandler: ((e: KeyboardEvent) => void) | null = null;

watch(() => props.visible, (newVal) => {
  if (newVal) {
    escHandler = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !props.loading) {
        handleCancel();
      }
    };
    document.addEventListener("keydown", escHandler);
  } else {
    if (escHandler) {
      document.removeEventListener("keydown", escHandler);
      escHandler = null;
    }
  }
});
</script>

<style scoped>
.confirm-dialog-overlay {
  /* 复用全局 .modal-overlay 的布局和视觉，仅轻微提升层级以确保在普通模态框之上 */
  z-index: 10001;
}

.confirm-dialog-content {
  max-width: 440px;
  padding: 32px 32px 28px;
  text-align: center;
}

.confirm-dialog-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  animation: icon-pulse 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) 0.2s both;
  transform-origin: center center;
}

@keyframes icon-pulse {
  0% {
    opacity: 0;
    transform: scale(0.3) rotate(-180deg);
  }
  50% {
    transform: scale(1.1) rotate(5deg);
  }
  100% {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }
}

.confirm-dialog-icon svg {
  width: 32px;
  height: 32px;
}

.confirm-dialog-icon--danger {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(220, 38, 38, 0.15));
  color: #ef4444;
  box-shadow: 
    0 0 0 8px rgba(239, 68, 68, 0.08),
    0 8px 24px rgba(239, 68, 68, 0.2);
}

.confirm-dialog-icon--warning {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.15));
  color: #f59e0b;
  box-shadow: 
    0 0 0 8px rgba(245, 158, 11, 0.08),
    0 8px 24px rgba(245, 158, 11, 0.2);
}

.confirm-dialog-icon--info {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(37, 99, 235, 0.15));
  color: #3b82f6;
  box-shadow: 
    0 0 0 8px rgba(59, 130, 246, 0.08),
    0 8px 24px rgba(59, 130, 246, 0.2);
}

.confirm-dialog-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--app-text-strong, #0f172a);
  margin: 0 0 12px 0;
  letter-spacing: -0.02em;
  line-height: 1.3;
}

.confirm-dialog-message {
  font-size: 15px;
  color: var(--app-muted, #64748b);
  line-height: 1.6;
  margin: 0 0 28px 0;
  word-break: break-word;
}

.confirm-dialog-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 8px;
}

.confirm-dialog-button {
  min-width: 100px;
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  position: relative;
  overflow: hidden;
}

.confirm-dialog-button::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: translate(-50%, -50%);
  transition: width 0.4s ease, height 0.4s ease;
}

.confirm-dialog-button:active::before {
  width: 300px;
  height: 300px;
}


.confirm-dialog-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none !important;
  pointer-events: none;
}

.confirm-dialog-button--cancel {
  background: rgba(241, 245, 249, 0.8);
  color: #475569;
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.confirm-dialog-button--cancel:hover:not(:disabled) {
  background: rgba(241, 245, 249, 1);
  color: #334155;
  transform: translateY(-2px);
  box-shadow: 
    0 6px 16px rgba(0, 0, 0, 0.12),
    0 3px 8px rgba(0, 0, 0, 0.08);
}

.confirm-dialog-button--cancel:active:not(:disabled) {
  transform: translateY(0) scale(0.96);
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.08),
    0 1px 4px rgba(0, 0, 0, 0.04);
}

.confirm-dialog-button--confirm {
  color: #ffffff;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.1),
    0 2px 6px rgba(0, 0, 0, 0.06);
}

.confirm-dialog-button--danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.confirm-dialog-button--danger:hover:not(:disabled) {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  transform: translateY(-2px);
  box-shadow: 
    0 10px 24px rgba(239, 68, 68, 0.35),
    0 5px 12px rgba(239, 68, 68, 0.25);
}

.confirm-dialog-button--danger:active:not(:disabled) {
  transform: translateY(0) scale(0.96);
  box-shadow: 
    0 2px 8px rgba(239, 68, 68, 0.25),
    0 1px 4px rgba(239, 68, 68, 0.15);
}

.confirm-dialog-button--warning {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.confirm-dialog-button--warning:hover:not(:disabled) {
  background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
  transform: translateY(-2px);
  box-shadow: 
    0 10px 24px rgba(245, 158, 11, 0.35),
    0 5px 12px rgba(245, 158, 11, 0.25);
}

.confirm-dialog-button--warning:active:not(:disabled) {
  transform: translateY(0) scale(0.96);
  box-shadow: 
    0 2px 8px rgba(245, 158, 11, 0.25),
    0 1px 4px rgba(245, 158, 11, 0.15);
}

.confirm-dialog-button--info {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.confirm-dialog-button--info:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-2px);
  box-shadow: 
    0 10px 24px rgba(59, 130, 246, 0.35),
    0 5px 12px rgba(59, 130, 246, 0.25);
}

.confirm-dialog-button--info:active:not(:disabled) {
  transform: translateY(0) scale(0.96);
  box-shadow: 
    0 2px 8px rgba(59, 130, 246, 0.25),
    0 1px 4px rgba(59, 130, 246, 0.15);
}

</style>

