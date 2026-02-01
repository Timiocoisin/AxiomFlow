<template>
  <button
    class="theme-toggle-button"
    :class="{ 'theme-toggle-button--dark': isDark }"
    type="button"
    :aria-label="isDark ? $t('theme.switchToLight') : $t('theme.switchToDark')"
    @click="handleToggle"
  >
    <div class="theme-toggle-button__container">
      <!-- 太阳图标 -->
      <svg
        class="theme-toggle-button__icon theme-toggle-button__icon--sun"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M12 2V4M12 20V22M4 12H2M22 12H20M19.07 4.93L17.66 6.34M6.34 17.66L4.93 19.07M19.07 19.07L17.66 17.66M6.34 6.34L4.93 4.93" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <!-- 月亮图标 -->
      <svg
        class="theme-toggle-button__icon theme-toggle-button__icon--moon"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  modelValue?: 'light' | 'dark';
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: 'light',
});

const emit = defineEmits<{
  'update:modelValue': [value: 'light' | 'dark'];
  'change': [value: 'light' | 'dark'];
}>();

const isDark = computed(() => props.modelValue === 'dark');

const handleToggle = () => {
  const newTheme = isDark.value ? 'light' : 'dark';
  emit('update:modelValue', newTheme);
  emit('change', newTheme);
};
</script>

<style scoped>
.theme-toggle-button {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  padding: 0;
  margin: 0;
  border: none;
  border-radius: 12px;
  background: var(--color-surface-2, rgba(255, 255, 255, 0.8));
  backdrop-filter: blur(var(--blur-md, 12px)) saturate(var(--sat-md, 160%));
  -webkit-backdrop-filter: blur(var(--blur-md, 12px)) saturate(var(--sat-md, 160%));
  box-shadow: 
    var(--shadow-xs, 0 1px 3px rgba(0, 0, 0, 0.04)),
    0 2px 8px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.theme-toggle-button::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 12px;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.4) 0%,
    rgba(255, 255, 255, 0.1) 100%
  );
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.theme-toggle-button:hover {
  transform: translateY(-1px);
  box-shadow: 
    var(--shadow-sm, 0 4px 16px rgba(0, 0, 0, 0.05)),
    0 4px 12px rgba(0, 0, 0, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
  background: var(--color-surface-1, rgba(255, 255, 255, 0.95));
}

.theme-toggle-button:hover::before {
  opacity: 1;
}

.theme-toggle-button:active {
  transform: translateY(0);
  box-shadow: 
    0 2px 6px rgba(0, 0, 0, 0.1),
    0 1px 3px rgba(0, 0, 0, 0.14),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

/* 深色模式样式 */
.theme-toggle-button--dark {
  background: var(--color-surface-2, rgba(30, 41, 59, 0.9));
  box-shadow: 
    var(--shadow-xs, 0 1px 2px rgba(15, 23, 42, 0.7)),
    0 2px 8px rgba(0, 0, 0, 0.24),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.theme-toggle-button--dark::before {
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.1) 0%,
    rgba(255, 255, 255, 0.05) 100%
  );
}

.theme-toggle-button--dark:hover {
  background: var(--color-surface-1, rgba(15, 23, 42, 0.96));
  box-shadow: 
    var(--shadow-sm, 0 6px 18px rgba(15, 23, 42, 0.8)),
    0 4px 12px rgba(0, 0, 0, 0.32),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.theme-toggle-button--dark:active {
  box-shadow: 
    0 2px 6px rgba(0, 0, 0, 0.28),
    0 1px 3px rgba(0, 0, 0, 0.36),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.theme-toggle-button__container {
  position: relative;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.theme-toggle-button__icon {
  position: absolute;
  width: 20px;
  height: 20px;
  color: var(--color-text-muted, #64748b);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
}

.theme-toggle-button--dark .theme-toggle-button__icon {
  color: var(--color-text-muted, #9ca3af);
}

/* 太阳图标 */
.theme-toggle-button__icon--sun {
  opacity: 1;
  transform: rotate(0deg) scale(1);
}

.theme-toggle-button--dark .theme-toggle-button__icon--sun {
  opacity: 0;
  transform: rotate(90deg) scale(0.5);
}

/* 月亮图标 */
.theme-toggle-button__icon--moon {
  opacity: 0;
  transform: rotate(-90deg) scale(0.5);
}

.theme-toggle-button--dark .theme-toggle-button__icon--moon {
  opacity: 1;
  transform: rotate(0deg) scale(1);
}

/* 焦点样式 */
.theme-toggle-button:focus-visible {
  outline: 2px solid var(--color-primary, #6366f1);
  outline-offset: 2px;
}
</style>
