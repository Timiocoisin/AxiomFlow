<template>
  <div class="loading-icon" :class="{ 'loading-icon--spinning': spinning }">
    <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <!-- 外圈 -->
      <circle
        cx="32"
        cy="32"
        r="28"
        stroke="url(#loadingGradient)"
        stroke-width="3"
        stroke-linecap="round"
        stroke-dasharray="44 176"
        stroke-dashoffset="0"
        fill="none"
        opacity="0.3"
      />
      <!-- 内圈旋转 -->
      <circle
        cx="32"
        cy="32"
        r="20"
        stroke="url(#loadingGradient)"
        stroke-width="2.5"
        stroke-linecap="round"
        stroke-dasharray="31.4 125.6"
        stroke-dashoffset="0"
        fill="none"
        class="loading-circle"
      />
      <!-- 中心点 -->
      <circle cx="32" cy="32" r="4" fill="url(#loadingGradient)" opacity="0.8" />
      <defs>
        <linearGradient id="loadingGradient" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#3b82f6" />
          <stop offset="50%" stop-color="#8b5cf6" />
          <stop offset="100%" stop-color="#6366f1" />
        </linearGradient>
      </defs>
    </svg>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  spinning?: boolean;
}>();
</script>

<style scoped>
.loading-icon {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-icon svg {
  width: 100%;
  height: 100%;
}

.loading-circle {
  animation: rotate 1.5s linear infinite;
  transform-origin: 32px 32px;
}

.loading-icon--spinning svg {
  animation: rotate-slow 3s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
    stroke-dashoffset: 0;
  }
  to {
    transform: rotate(360deg);
    stroke-dashoffset: -157;
  }
}

@keyframes rotate-slow {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>

