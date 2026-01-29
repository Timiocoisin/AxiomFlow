<template>
  <TransitionGroup name="toast" tag="div" class="toast-container">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      :class="['toast', `toast-${toast.type}`]"
    >
      <div class="toast-icon">
        <svg v-if="toast.type === 'success'" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <svg v-else-if="toast.type === 'error'" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <svg v-else-if="toast.type === 'warning'" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <div class="toast-content">
        <div class="toast-title">{{ toast.title }}</div>
        <div v-if="toast.message" class="toast-message">{{ toast.message }}</div>
      </div>
      <button class="toast-close" @click="removeToast(toast.id)">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </TransitionGroup>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";

export interface Toast {
  id: string;
  type: "success" | "error" | "warning" | "info";
  title: string;
  message?: string;
  duration?: number;
}

const toasts = ref<Toast[]>([]);

let toastIdCounter = 0;

const addToast = (toast: Omit<Toast, "id">) => {
  const id = `toast-${++toastIdCounter}`;
  const newToast: Toast = {
    id,
    duration: 3000, // 默认3秒自动消失
    ...toast,
  };
  toasts.value.push(newToast);

  if (newToast.duration && newToast.duration > 0) {
    setTimeout(() => {
      removeToast(id);
    }, newToast.duration);
  }
};

const removeToast = (id: string) => {
  const index = toasts.value.findIndex((t) => t.id === id);
  if (index > -1) {
    toasts.value.splice(index, 1);
  }
};

// 全局方法
const showToast = (toast: Omit<Toast, "id">) => {
  addToast(toast);
};

// 导出方法供外部使用
defineExpose({
  showToast,
  addToast,
  removeToast,
});

// 全局事件监听
let toastContainer: any = null;

onMounted(() => {
  // 创建全局 toast 容器
  toastContainer = document.createElement("div");
  toastContainer.id = "toast-global-container";
  document.body.appendChild(toastContainer);

  // 监听全局 toast 事件
  window.addEventListener("show-toast", ((e: CustomEvent) => {
    addToast(e.detail);
  }) as EventListener);
});

onUnmounted(() => {
  if (toastContainer && document.body.contains(toastContainer)) {
    document.body.removeChild(toastContainer);
  }
  window.removeEventListener("show-toast", () => {});
});

// 导出全局函数
(window as any).showToast = showToast;
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 80px; /* 避免挡住顶部导航栏（导航栏高度约64px + 16px间距） */
  right: 24px;
  z-index: 9999; /* 低于导航栏的 z-index: 100，但高于其他内容 */
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none;
  max-width: 420px;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 18px 22px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 16px;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.12),
    0 8px 16px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(0, 0, 0, 0.04);
  pointer-events: auto;
  min-width: 320px;
  max-width: 440px;
  animation: toast-slide-in 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.9);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.toast {
  /* Default accent for fallback; overwritten per type below */
  --toast-accent: var(--color-primary, #6366f1);
  --toast-accent-soft: color-mix(in srgb, var(--toast-accent) 12%, transparent);
}

@keyframes toast-slide-in {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.toast-success {
  --toast-accent: var(--color-success, #10b981);
  border-left: 5px solid var(--toast-accent);
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.95) 0%,
    color-mix(in srgb, var(--toast-accent) 10%, #ffffff) 60%,
    rgba(255, 255, 255, 0.92) 100%
  );
  box-shadow: 
    0 20px 40px rgba(16, 185, 129, 0.18),
    0 8px 16px rgba(16, 185, 129, 0.12),
    0 0 0 1px rgba(16, 185, 129, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
}

.toast-error {
  --toast-accent: var(--color-danger, #ef4444);
  border-left: 5px solid var(--toast-accent);
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.95) 0%,
    color-mix(in srgb, var(--toast-accent) 10%, #ffffff) 60%,
    rgba(255, 255, 255, 0.92) 100%
  );
  box-shadow: 
    0 20px 40px rgba(239, 68, 68, 0.18),
    0 8px 16px rgba(239, 68, 68, 0.12),
    0 0 0 1px rgba(239, 68, 68, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
}

.toast-warning {
  --toast-accent: var(--color-warning, #f59e0b);
  border-left: 5px solid var(--toast-accent);
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.95) 0%,
    color-mix(in srgb, var(--toast-accent) 12%, #ffffff) 60%,
    rgba(255, 255, 255, 0.92) 100%
  );
  box-shadow: 
    0 20px 40px rgba(245, 158, 11, 0.18),
    0 8px 16px rgba(245, 158, 11, 0.12),
    0 0 0 1px rgba(245, 158, 11, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
}

.toast-info {
  --toast-accent: var(--color-info, #3b82f6);
  border-left: 5px solid var(--toast-accent);
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.95) 0%,
    color-mix(in srgb, var(--toast-accent) 10%, #ffffff) 60%,
    rgba(255, 255, 255, 0.92) 100%
  );
  box-shadow: 
    0 20px 40px rgba(59, 130, 246, 0.18),
    0 8px 16px rgba(59, 130, 246, 0.12),
    0 0 0 1px rgba(59, 130, 246, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
}

.toast-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  margin-top: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: toast-icon-pop 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes toast-icon-pop {
  0% { transform: scale(0.7); opacity: 0.6; }
  60% { transform: scale(1.08); opacity: 1; }
  100% { transform: scale(1); opacity: 1; }
}

.toast-success .toast-icon {
  color: var(--toast-accent);
  background: var(--toast-accent-soft);
}

.toast-success .toast-icon svg {
  width: 20px;
  height: 20px;
}

.toast-error .toast-icon {
  color: var(--toast-accent);
  background: var(--toast-accent-soft);
}

.toast-error .toast-icon svg {
  width: 20px;
  height: 20px;
}

.toast-warning .toast-icon {
  color: var(--toast-accent);
  background: var(--toast-accent-soft);
}

.toast-warning .toast-icon svg {
  width: 20px;
  height: 20px;
}

.toast-info .toast-icon {
  color: var(--toast-accent);
  background: var(--toast-accent-soft);
}

.toast-info .toast-icon svg {
  width: 20px;
  height: 20px;
}

.toast-content {
  flex: 1;
  min-width: 0;
}

.toast-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text-strong, #0f172a);
  margin-bottom: 4px;
  line-height: 1.4;
}

.toast-message {
  font-size: 13px;
  color: var(--app-muted, #64748b);
  line-height: 1.5;
}

.toast-close {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  padding: 0;
  background: none;
  border: none;
  cursor: pointer;
  color: color-mix(in srgb, var(--app-muted, #64748b) 70%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s ease;
  margin-top: -2px;
}

.toast-close:hover {
  color: var(--app-muted, #64748b);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.toast-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.toast-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.toast-move {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@media (max-width: 640px) {
  .toast-container {
    top: 16px;
    right: 16px;
    left: 16px;
    max-width: none;
  }

  .toast {
    min-width: auto;
    max-width: none;
  }
}
</style>

