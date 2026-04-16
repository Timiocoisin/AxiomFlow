<template>
  <main class="flex-grow container mx-auto px-4 py-8 max-w-7xl" id="main-content">
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">我的文档</h1>
        <p class="text-slate-500 mt-1">管理和查看您的 PDF 翻译历史（截至 {{ asOfDate }}）</p>
      </div>
      <button
        class="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-xl font-semibold transition-all shadow-lg shadow-indigo-600/20"
        type="button"
        @click="$emit('new-translation')"
      >
        <Icon icon="ph:plus-bold" />
        新建翻译
      </button>
    </div>

    <div class="glass rounded-2xl p-4 mb-6 flex flex-col md:flex-row gap-4 items-center">
      <div class="relative flex-grow w-full">
        <Icon class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-lg" icon="ph:magnifying-glass-bold" />
        <input
          class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl py-2.5 pl-11 pr-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
          placeholder="搜索文件名..."
          type="text"
        />
      </div>
      <div class="flex gap-2 w-full md:w-auto">
        <select class="bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl py-2.5 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all flex-grow md:flex-none">
          <option value="">全部状态</option>
          <option value="pending">待翻译</option>
          <option value="processing">翻译中</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
        </select>
        <select class="bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl py-2.5 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all flex-grow md:flex-none">
          <option value="">所有时间</option>
          <option value="today">今天</option>
          <option value="week">最近一周</option>
          <option value="month">最近一月</option>
        </select>
      </div>
    </div>

    <div class="glass rounded-2xl overflow-hidden shadow-xl border dark:border-slate-800">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-50/50 dark:bg-slate-900/50 border-b dark:border-slate-800">
              <th class="px-6 py-4 text-sm font-semibold text-slate-500">文档名称</th>
              <th class="px-6 py-4 text-sm font-semibold text-slate-500">上传日期</th>
              <th class="px-6 py-4 text-sm font-semibold text-slate-500">文件大小</th>
              <th class="px-6 py-4 text-sm font-semibold text-slate-500">语言对</th>
              <th class="px-6 py-4 text-sm font-semibold text-slate-500">状态</th>
              <th class="px-6 py-4 text-sm font-semibold text-slate-500 text-right">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y dark:divide-slate-800">
            <tr class="hover:bg-slate-50/50 dark:hover:bg-slate-900/30 transition-colors">
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg flex items-center justify-center text-indigo-600">
                    <Icon class="text-2xl" icon="ph:file-pdf-bold" />
                  </div>
                  <div>
                    <p class="font-medium">2026年第一季度财务报告.pdf</p>
                    <p class="text-xs text-slate-500">ID: DOC-98234</p>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 text-sm text-slate-500">2026-04-14 10:30</td>
              <td class="px-6 py-4 text-sm text-slate-500">4.2 MB</td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-2 text-sm font-medium">
                  <span>中文</span>
                  <Icon class="text-xs text-slate-400" icon="ph:arrow-right-bold" />
                  <span>英文</span>
                </div>
              </td>
              <td class="px-6 py-4">
                <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                  <span class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                  已完成
                </span>
              </td>
              <td class="px-6 py-4 text-right">
                <div class="flex justify-end gap-2">
                  <button class="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 rounded-lg transition-all" title="对比预览" type="button" @click="$emit('open-preview')">
                    <Icon class="text-xl" icon="ph:layout-bold" />
                  </button>
                  <button class="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 rounded-lg transition-all" title="查看详情" type="button" @click="openDetails('2026年第一季度财务报告')">
                    <Icon class="text-xl" icon="ph:eye-bold" />
                  </button>
                  <button class="p-2 text-slate-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/30 rounded-lg transition-all" title="下载结果" type="button">
                    <Icon class="text-xl" icon="ph:download-simple-bold" />
                  </button>
                  <button class="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-all" title="删除" type="button">
                    <Icon class="text-xl" icon="ph:trash-bold" />
                  </button>
                </div>
              </td>
            </tr>

            <tr class="hover:bg-slate-50/50 dark:hover:bg-slate-900/30 transition-colors">
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center text-blue-600">
                    <Icon class="text-2xl" icon="ph:file-pdf-bold" />
                  </div>
                  <div>
                    <p class="font-medium">人工智能未来展望白皮书.pdf</p>
                    <p class="text-xs text-slate-500">ID: DOC-98235</p>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 text-sm text-slate-500">2026-04-15 09:15</td>
              <td class="px-6 py-4 text-sm text-slate-500">12.8 MB</td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-2 text-sm font-medium">
                  <span>英文</span>
                  <Icon class="text-xs text-slate-400" icon="ph:arrow-right-bold" />
                  <span>日文</span>
                </div>
              </td>
              <td class="px-6 py-4">
                <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                  <Icon class="animate-spin text-sm" icon="ph:spinner-gap-bold" />
                  翻译中 65%
                </span>
              </td>
              <td class="px-6 py-4 text-right">
                <div class="flex justify-end gap-2 text-slate-300 dark:text-slate-700">
                  <button class="p-2 cursor-not-allowed" disabled type="button"><Icon class="text-xl" icon="ph:eye-bold" /></button>
                  <button class="p-2 cursor-not-allowed" disabled type="button"><Icon class="text-xl" icon="ph:download-simple-bold" /></button>
                  <button class="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-all" type="button"><Icon class="text-xl" icon="ph:trash-bold" /></button>
                </div>
              </td>
            </tr>

            <tr class="hover:bg-slate-50/50 dark:hover:bg-slate-900/30 transition-colors">
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-lg flex items-center justify-center text-red-600">
                    <Icon class="text-2xl" icon="ph:file-pdf-bold" />
                  </div>
                  <div>
                    <p class="font-medium">加密合同草案_v2.pdf</p>
                    <p class="text-xs text-slate-500">ID: DOC-98236</p>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 text-sm text-slate-500">2026-04-15 14:00</td>
              <td class="px-6 py-4 text-sm text-slate-500">1.5 MB</td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-2 text-sm font-medium">
                  <span>日文</span>
                  <Icon class="text-xs text-slate-400" icon="ph:arrow-right-bold" />
                  <span>中文</span>
                </div>
              </td>
              <td class="px-6 py-4">
                <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400">
                  <Icon class="text-sm" icon="ph:warning-circle-bold" />
                  翻译失败
                </span>
              </td>
              <td class="px-6 py-4 text-right">
                <div class="flex justify-end gap-2">
                  <button class="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 rounded-lg transition-all" title="重新翻译" type="button">
                    <Icon class="text-xl" icon="ph:arrows-clockwise-bold" />
                  </button>
                  <button class="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-all" title="删除" type="button">
                    <Icon class="text-xl" icon="ph:trash-bold" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="px-6 py-4 bg-slate-50/50 dark:bg-slate-900/50 border-t dark:border-slate-800 flex items-center justify-between">
        <span class="text-sm text-slate-500">显示 1 到 3 项，共 12 项文档</span>
        <div class="flex gap-2">
          <button class="px-3 py-1.5 rounded-lg border dark:border-slate-800 hover:bg-white dark:hover:bg-slate-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed" disabled type="button">
            <Icon icon="ph:caret-left-bold" />
          </button>
          <button class="px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-medium" type="button">1</button>
          <button class="px-3 py-1.5 rounded-lg border dark:border-slate-800 hover:bg-white dark:hover:bg-slate-800 transition-colors" type="button">2</button>
          <button class="px-3 py-1.5 rounded-lg border dark:border-slate-800 hover:bg-white dark:hover:bg-slate-800 transition-colors" type="button">3</button>
          <button class="px-3 py-1.5 rounded-lg border dark:border-slate-800 hover:bg-white dark:hover:bg-slate-800 transition-colors" type="button">
            <Icon icon="ph:caret-right-bold" />
          </button>
        </div>
      </div>
    </div>

    <div class="fixed inset-0 z-[100] p-4" :class="showDetails ? 'flex items-center justify-center' : 'hidden'">
      <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" @click="closeDetails"></div>
      <div class="relative glass w-full max-w-4xl max-h-[90vh] rounded-3xl overflow-hidden flex flex-col shadow-2xl">
        <div class="p-6 border-b dark:border-slate-800 flex justify-between items-center">
          <div>
            <h2 class="text-xl font-bold">{{ modalTitle }}</h2>
            <p class="text-sm text-slate-500">原文与译文实时对比</p>
          </div>
          <button class="w-10 h-10 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center justify-center transition-colors" type="button" @click="closeDetails">
            <Icon class="text-xl" icon="ph:x-bold" />
          </button>
        </div>
        <div class="p-6 overflow-y-auto flex-grow bg-slate-50/50 dark:bg-slate-950/50">
          <p class="text-slate-500">这里展示文档对比预览（原型占位）。</p>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Icon } from "@iconify/vue";

defineProps<{
  asOfDate: string;
}>();

defineEmits<{
  (e: "new-translation"): void;
  (e: "open-preview"): void;
}>();

const showDetails = ref(false);
const modalTitle = ref("文档翻译详情");

function openDetails(name: string) {
  modalTitle.value = `${name} - 翻译对比`;
  showDetails.value = true;
}

function closeDetails() {
  showDetails.value = false;
}
</script>
