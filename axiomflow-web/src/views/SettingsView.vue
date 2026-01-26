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
          </div>
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
import { useUserStore } from "@/stores/user";

const userStore = useUserStore();
</script>


