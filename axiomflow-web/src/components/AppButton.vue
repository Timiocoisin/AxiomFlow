<template>
  <button class="app-btn" :class="{ primary }">
    <slot />
  </button>
</template>

<script setup lang="ts">
defineProps<{ primary?: boolean }>();
</script>

<style scoped>
.app-btn {
  border: 1px solid rgba(226, 232, 240, 0.8);
  background: rgba(255, 255, 255, 0.9);
  color: #475569;
  padding: 10px 14px;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 500;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.app-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.4);
  background: rgba(255, 255, 255, 1);
  color: #3b82f6;
}

.app-btn.primary {
  border-color: rgba(59, 130, 246, 0.6);
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: #ffffff;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
}

.app-btn.primary:hover {
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
  transform: translateY(-2px);
  border-color: rgba(59, 130, 246, 0.8);
}
</style>


