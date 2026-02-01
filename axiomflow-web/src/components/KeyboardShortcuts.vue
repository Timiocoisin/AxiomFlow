<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="visible"
        class="shortcuts-modal-overlay"
        @click.self="close"
        role="dialog"
        aria-modal="true"
        aria-labelledby="shortcuts-title"
      >
        <div class="shortcuts-modal glass-card" ref="modalRef">
          <div class="shortcuts-header">
            <h2 id="shortcuts-title">{{ $t('shortcuts.title') || '快捷键' }}</h2>
            <button
              class="shortcuts-close"
              @click="close"
              :aria-label="$t('common.close') || '关闭'"
            >
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
          </div>
          <div class="shortcuts-content">
            <div v-for="section in shortcuts" :key="section.category" class="shortcuts-section">
              <h3 class="shortcuts-category">{{ section.category }}</h3>
              <ul class="shortcuts-list">
                <li v-for="shortcut in section.items" :key="shortcut.key" class="shortcuts-item">
                  <div class="shortcuts-description">{{ shortcut.description }}</div>
                  <div class="shortcuts-keys">
                    <kbd v-for="(key, index) in shortcut.keys" :key="index" class="shortcut-key">
                      {{ key }}
                    </kbd>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import { Teleport } from 'vue';
import { useI18n } from 'vue-i18n';

interface ShortcutItem {
  description: string;
  keys: string[];
}

interface ShortcutSection {
  category: string;
  items: ShortcutItem[];
}

const props = defineProps<{
  visible: boolean;
  shortcuts?: ShortcutSection[];
}>();

const emit = defineEmits<{
  'update:visible': [value: boolean];
}>();

const { t } = useI18n();
const modalRef = ref<HTMLElement | null>(null);

const defaultShortcuts: ShortcutSection[] = [
  {
    category: t('shortcuts.navigation') || '导航',
    items: [
      { description: t('shortcuts.search') || '搜索文档', keys: ['/', 'Ctrl+F', 'Cmd+F'] },
      { description: t('shortcuts.clearSearch') || '清空搜索', keys: ['Esc'] },
      { description: t('shortcuts.navigateCards') || '导航文档卡片', keys: ['↑', '↓', '←', '→'] },
      { description: t('shortcuts.openDocument') || '打开文档', keys: ['Enter', 'Space'] },
    ]
  },
  {
    category: t('shortcuts.actions') || '操作',
    items: [
      { description: t('shortcuts.deleteDocument') || '删除文档', keys: ['Delete'] },
      { description: t('shortcuts.selectMode') || '进入选择模式', keys: ['Ctrl+A', 'Cmd+A'] },
      { description: t('shortcuts.closeModal') || '关闭对话框', keys: ['Esc'] },
    ]
  },
  {
    category: t('shortcuts.general') || '通用',
    items: [
      { description: t('shortcuts.showShortcuts') || '显示快捷键', keys: ['?'] },
      { description: t('shortcuts.toggleTheme') || '切换主题', keys: ['Ctrl+Shift+T', 'Cmd+Shift+T'] },
    ]
  }
];

const shortcuts = props.shortcuts || defaultShortcuts;

const close = () => {
  emit('update:visible', false);
};

// 键盘事件处理
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.visible) {
    close();
  }
};

watch(() => props.visible, (newVal) => {
  if (newVal) {
    nextTick(() => {
      modalRef.value?.focus();
    });
    document.addEventListener('keydown', handleKeydown);
  } else {
    document.removeEventListener('keydown', handleKeydown);
  }
});
</script>

<style scoped>
.shortcuts-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  padding: var(--spacing-lg, 16px);
}

.shortcuts-modal {
  max-width: 600px;
  width: 100%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  outline: none;
  overflow: hidden;
  /* 确保内容区域可以滚动，但保持底部可见 */
}

.shortcuts-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-xl, 24px);
  border-bottom: 1px solid var(--color-border, rgba(226, 232, 240, 0.8));
}

.shortcuts-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-strong, #0f172a);
}

.shortcuts-close {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: var(--radius-md, 12px);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--color-text-muted, #64748b);
  transition: all 0.2s ease;
}

.shortcuts-close:hover {
  background: var(--color-surface-2, rgba(255, 255, 255, 0.75));
  color: var(--color-text, #1e293b);
}

.shortcuts-close svg {
  width: 18px;
  height: 18px;
}

.shortcuts-content {
  padding: var(--spacing-xl, 24px);
  overflow-y: auto;
  flex: 1;
  min-height: 0;
  /* 使用 scroll-padding-bottom 确保最后一行可见 */
  scroll-padding-bottom: var(--spacing-xl, 24px);
  /* 确保滚动条样式 */
  scrollbar-width: thin;
  scrollbar-color: var(--color-border, rgba(226, 232, 240, 0.8)) transparent;
}

.shortcuts-content::-webkit-scrollbar {
  width: 6px;
}

.shortcuts-content::-webkit-scrollbar-track {
  background: transparent;
}

.shortcuts-content::-webkit-scrollbar-thumb {
  background: var(--color-border, rgba(226, 232, 240, 0.8));
  border-radius: 3px;
}

.shortcuts-content::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-muted, #64748b);
}

.shortcuts-section {
  margin-bottom: var(--spacing-2xl, 32px);
}

.shortcuts-section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
}

.shortcuts-category {
  margin: 0 0 var(--spacing-lg, 16px) 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-strong, #0f172a);
}

.shortcuts-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md, 12px);
}

.shortcuts-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md, 12px);
  border-radius: var(--radius-md, 12px);
  background: var(--color-surface-2, rgba(255, 255, 255, 0.75));
  transition: background 0.2s ease;
}

.shortcuts-item:hover {
  background: var(--color-surface-1, rgba(255, 255, 255, 0.95));
}

.shortcuts-description {
  font-size: 14px;
  color: var(--color-text, #1e293b);
  flex: 1;
}

.shortcuts-keys {
  display: flex;
  gap: 4px;
  align-items: center;
}

.shortcut-key {
  display: inline-block;
  padding: 4px 8px;
  font-size: 12px;
  font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
  background: var(--color-surface-0, #ffffff);
  border: 1px solid var(--color-border, rgba(226, 232, 240, 0.8));
  border-radius: 4px;
  color: var(--color-text-strong, #0f172a);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  min-width: 24px;
  text-align: center;
}

[data-theme="dark"] .shortcuts-header h2,
[data-theme="dark"] .shortcuts-category {
  color: var(--color-text-strong, #e5e7eb);
}

[data-theme="dark"] .shortcuts-description {
  color: var(--color-text, #e5e7eb);
}

[data-theme="dark"] .shortcuts-item {
  background: var(--color-surface-2, rgba(30, 41, 59, 0.9));
}

[data-theme="dark"] .shortcuts-item:hover {
  background: var(--color-surface-1, rgba(15, 23, 42, 0.96));
}

[data-theme="dark"] .shortcut-key {
  background: var(--color-surface-0, #020617);
  border-color: var(--color-border, rgba(51, 65, 85, 0.9));
  color: var(--color-text-strong, #e5e7eb);
}

@media (max-width: 768px) {
  .shortcuts-modal {
    max-width: 100%;
    max-height: 90vh;
  }

  .shortcuts-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm, 8px);
  }

  .shortcuts-keys {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>

