<template>
  <div class="app-card">
    <slot />
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.app-card {
  border-radius: 16px;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.95) 0%, 
    rgba(250, 245, 255, 0.92) 25%,
    rgba(240, 249, 255, 0.92) 50%,
    rgba(255, 250, 240, 0.92) 75%,
    rgba(255, 255, 255, 0.95) 100%);
  background-size: 200% 200%;
  background-position: 0% 0%;
  animation: gradient-shift 20s ease infinite;
  border: 1px solid rgba(226, 232, 240, 0.6);
  box-shadow: 
    0 4px 16px rgba(99, 102, 241, 0.06),
    0 2px 8px rgba(139, 92, 246, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
}

@keyframes gradient-shift {
  0%, 100% {
    background-position: 0% 0%;
  }
  50% {
    background-position: 100% 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-card {
    animation: none;
  }
}
</style>


