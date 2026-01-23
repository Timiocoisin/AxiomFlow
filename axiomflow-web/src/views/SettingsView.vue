<template>
  <section class="settings glass-card">
    <h2>设置</h2>
    
    <!-- 账号设置 -->
    <div class="settings-section">
      <h3 class="settings-section-title">账号设置</h3>
      <div class="settings-item">
        <div class="settings-item-label">
          <span>邮箱地址</span>
        </div>
        <div class="settings-item-content">
          <div class="email-display">
            <span class="email-text">{{ userStore.user?.email }}</span>
            <span v-if="userStore.user?.email_verified === false" class="email-verify-badge unverified">未验证</span>
            <span v-else-if="userStore.user?.email_verified === true" class="email-verify-badge verified">已验证</span>
          </div>
          <button
            v-if="userStore.user?.email_verified === false"
            class="resend-verify-button"
            @click="handleResendVerifyEmail"
            :disabled="resendingVerifyEmail"
          >
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 8L10.89 13.26C11.2187 13.4793 11.6049 13.5963 12 13.5963C12.3951 13.5963 12.7813 13.4793 13.11 13.26L21 8M5 19H19C19.5304 19 20.0391 18.7893 20.4142 18.4142C20.7893 18.0391 21 17.5304 21 17V7C21 6.46957 20.7893 5.96086 20.4142 5.58579C20.0391 5.21071 19.5304 5 19 5H5C4.46957 5 3.96086 5.21071 3.58579 5.58579C3.21071 5.96086 3 6.46957 3 7V17C3 17.5304 3.21071 18.0391 3.58579 18.4142C3.96086 18.7893 4.46957 19 5 19Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>{{ resendingVerifyEmail ? '发送中...' : '重新发送验证邮件' }}</span>
          </button>
          <p v-if="userStore.user?.email_verified === false" class="settings-item-hint">
            您的邮箱尚未验证。请点击上方按钮重新发送验证邮件，并在 24 小时内完成验证。
          </p>
        </div>
      </div>
    </div>

    <!-- 其他设置 -->
    <div class="settings-section">
      <h3 class="settings-section-title">其他设置</h3>
      <p class="settings-placeholder">在这里配置默认翻译引擎、语言风格与主题（浅色/深色/科研蓝）。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useUserStore } from "@/stores/user";
import { resendVerifyEmail } from "@/lib/api";
import { showToast } from "@/components/Toast";

const userStore = useUserStore();
const resendingVerifyEmail = ref(false);

const handleResendVerifyEmail = async () => {
  if (!userStore.user?.email || resendingVerifyEmail.value) return;
  
  resendingVerifyEmail.value = true;
  try {
    const result = await resendVerifyEmail({ email: userStore.user.email });
    showToast("success", "验证邮件已发送", result.message);
    // 如果后端提示「已完成验证」，前端同步更新状态
    if (result.message && result.message.includes("已完成验证")) {
      userStore.setEmailVerified(true);
    }
  } catch (error: any) {
    showToast("error", "发送失败", error.message || "请稍后重试");
  } finally {
    resendingVerifyEmail.value = false;
  }
};
</script>


