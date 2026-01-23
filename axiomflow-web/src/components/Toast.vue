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
    duration: 4000,
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
  top: 24px;
  right: 24px;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none;
  max-width: 420px;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 
    0 10px 25px rgba(0, 0, 0, 0.1),
    0 4px 10px rgba(0, 0, 0, 0.05);
  pointer-events: auto;
  min-width: 300px;
  max-width: 420px;
  animation: toast-slide-in 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.8);
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
  border-left: 4px solid #10b981;
  background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
  box-shadow: 
    0 10px 25px rgba(16, 185, 129, 0.15),
    0 4px 10px rgba(16, 185, 129, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.toast-error {
  border-left: 4px solid #ef4444;
  background: linear-gradient(135deg, #ffffff 0%, #fef2f2 100%);
  box-shadow: 
    0 10px 25px rgba(239, 68, 68, 0.15),
    0 4px 10px rgba(239, 68, 68, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.toast-warning {
  border-left: 4px solid #f59e0b;
  background: linear-gradient(135deg, #ffffff 0%, #fffbeb 100%);
  box-shadow: 
    0 10px 25px rgba(245, 158, 11, 0.15),
    0 4px 10px rgba(245, 158, 11, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.toast-info {
  border-left: 4px solid #3b82f6;
  background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%);
  box-shadow: 
    0 10px 25px rgba(59, 130, 246, 0.15),
    0 4px 10px rgba(59, 130, 246, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.toast-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  margin-top: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.toast-success .toast-icon {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.toast-success .toast-icon svg {
  width: 18px;
  height: 18px;
}

.toast-error .toast-icon {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.toast-error .toast-icon svg {
  width: 18px;
  height: 18px;
}

.toast-warning .toast-icon {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
}

.toast-warning .toast-icon svg {
  width: 18px;
  height: 18px;
}

.toast-info .toast-icon {
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
}

.toast-info .toast-icon svg {
  width: 18px;
  height: 18px;
}

.toast-content {
  flex: 1;
  min-width: 0;
}

.toast-title {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 4px;
  line-height: 1.4;
}

.toast-message {
  font-size: 13px;
  color: #64748b;
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
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s ease;
  margin-top: -2px;
}

.toast-close:hover {
  color: #64748b;
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

