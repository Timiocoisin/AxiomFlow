<template>
  <div class="verify-email-container">
    <div class="verify-email-card glass-card">
      <div v-if="!verified" class="verify-email-content">
        <div class="verify-email-header">
          <div class="verify-email-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="22,6 12,13 2,6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <h1 class="verify-email-title">验证邮箱地址</h1>
          <p class="verify-email-subtitle">正在验证您的邮箱地址...</p>
        </div>
        <div v-if="loading" class="verify-email-loading">
          <div class="loading-spinner"></div>
          <p>验证中，请稍候...</p>
        </div>
        <div v-if="error" class="verify-email-error">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 8v4M12 16h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <h3>验证失败</h3>
          <p>{{ error }}</p>
          <div class="verify-email-actions">
            <button class="auth-button" @click="handleResend">
              <span v-if="resending" class="loading-spinner"></span>
              <span>{{ resending ? "发送中..." : "重新发送验证邮件" }}</span>
            </button>
            <button class="auth-link" @click="goToDashboard">返回首页</button>
          </div>
        </div>
      </div>
      <div v-else class="verify-email-success">
        <div class="success-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <h1 class="verify-email-title">验证成功！</h1>
        <p class="verify-email-subtitle">您的邮箱地址已验证，现在可以正常使用所有功能了。</p>
        <button class="auth-button" @click="goToDashboard">前往首页</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { verifyEmail, sendEmailVerification } from "@/lib/api";
import { useUserStore } from "@/stores/user";

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const loading = ref(true);
const verified = ref(false);
const error = ref("");
const resending = ref(false);

const showToast = (type: "success" | "error" | "warning" | "info", title: string, message?: string) => {
  const event = new CustomEvent("show-toast", {
    detail: { type, title, message },
  });
  window.dispatchEvent(event);
};

const verifyToken = async (token: string) => {
  loading.value = true;
  error.value = "";
  
  try {
    const result = await verifyEmail({ token });
    verified.value = true;
    showToast("success", "验证成功", result.message);
    
    // 更新用户信息
    if (userStore.user) {
      userStore.user.email_verified = true;
      userStore.user.email_verified_at = new Date().toISOString();
      // 更新存储
      const storage = localStorage.getItem("auth_token") ? localStorage : sessionStorage;
      storage.setItem("user", JSON.stringify(userStore.user));
    }
  } catch (err: any) {
    error.value = err.message || "验证失败，请稍后重试";
    showToast("error", "验证失败", err.message);
  } finally {
    loading.value = false;
  }
};

const handleResend = async () => {
  if (!userStore.user?.email) {
    showToast("error", "错误", "无法获取邮箱地址");
    return;
  }
  
  resending.value = true;
  try {
    const result = await sendEmailVerification({ email: userStore.user.email });
    showToast("success", "发送成功", result.message);
    if (result.verification_url) {
      showToast("info", "开发环境提示", `验证链接：${result.verification_url}`);
    }
  } catch (err: any) {
    showToast("error", "发送失败", err.message);
  } finally {
    resending.value = false;
  }
};

const goToDashboard = () => {
  router.push("/");
};

onMounted(() => {
  const token = route.query.token as string;
  if (token) {
    verifyToken(token);
  } else {
    error.value = "缺少验证链接，请检查邮件中的链接是否正确";
    loading.value = false;
  }
});
</script>

<style scoped>
.verify-email-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0e7ff 50%, #f3e8ff 100%);
}

.verify-email-card {
  width: 100%;
  max-width: 500px;
  padding: 48px 40px;
  text-align: center;
}

.verify-email-header {
  margin-bottom: 32px;
}

.verify-email-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
  color: #6366f1;
}

.verify-email-icon svg {
  width: 100%;
  height: 100%;
}

.verify-email-title {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 12px;
  letter-spacing: -0.02em;
}

.verify-email-subtitle {
  font-size: 16px;
  color: #64748b;
  line-height: 1.6;
}

.verify-email-loading {
  padding: 40px 0;
}

.verify-email-loading .loading-spinner {
  width: 48px;
  height: 48px;
  margin: 0 auto 24px;
}

.verify-email-loading p {
  color: #64748b;
  font-size: 15px;
}

.verify-email-error {
  padding: 24px 0;
}

.verify-email-error svg {
  width: 64px;
  height: 64px;
  margin: 0 auto 24px;
  color: #ef4444;
}

.verify-email-error h3 {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 12px;
}

.verify-email-error p {
  color: #64748b;
  font-size: 15px;
  margin-bottom: 32px;
  line-height: 1.6;
}

.verify-email-actions {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.verify-email-success {
  padding: 24px 0;
}

.success-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 32px;
  color: #10b981;
}

.success-icon svg {
  width: 100%;
  height: 100%;
}

.auth-button {
  width: 100%;
  padding: 14px 28px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.auth-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3);
}

.auth-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-link {
  background: none;
  border: none;
  color: #6366f1;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  padding: 8px;
  text-decoration: underline;
  text-underline-offset: 4px;
}

.auth-link:hover {
  color: #8b5cf6;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>

