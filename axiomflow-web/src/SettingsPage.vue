<template>
  <main class="flex-grow container mx-auto px-4 py-8 max-w-5xl" id="main-content">
    <div class="flex flex-col md:flex-row gap-8">
      <aside class="w-full md:w-64 space-y-2">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-left transition-all"
          :class="
            activeTab === tab.id
              ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 font-semibold'
              : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400'
          "
          type="button"
          @click="activeTab = tab.id"
        >
          <Icon :icon="tab.icon" />
          {{ tab.label }}
        </button>
      </aside>

      <div class="flex-grow">
        <div class="glass rounded-2xl p-6 md:p-8 border dark:border-slate-800">
          <section v-if="activeTab === 'account'" class="space-y-8">
            <h2 class="text-2xl font-bold">账户设置</h2>
            <div class="flex items-center gap-6 pb-8 border-b dark:border-slate-800">
              <div class="relative group">
                <img alt="Avatar" class="w-24 h-24 rounded-2xl object-cover ring-4 ring-indigo-50 dark:ring-indigo-900/30" :src="avatarUrl" />
                <label class="absolute inset-0 flex items-center justify-center bg-black/50 text-white rounded-2xl opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity" for="settings-avatar-upload">
                  <Icon class="text-2xl" icon="ph:camera-bold" />
                </label>
                <input id="settings-avatar-upload" accept="image/*" class="hidden" type="file" @change="previewAvatar" />
              </div>
              <div>
                <h3 class="font-bold text-lg">Felix Zheng</h3>
                <p class="text-sm text-slate-500">上次登录：{{ serviceTime }}</p>
                <label class="mt-2 inline-block text-sm text-indigo-600 font-medium hover:underline cursor-pointer" for="settings-avatar-upload">
                  上传新头像
                </label>
              </div>
            </div>
            <form class="space-y-6" @submit.prevent="saveSettings">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="space-y-2">
                  <label class="text-sm font-semibold">用户名</label>
                  <input class="w-full px-4 py-2.5 rounded-xl border dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 focus:ring-2 focus:ring-indigo-500 outline-none transition-all" type="text" value="Felix Zheng" />
                </div>
                <div class="space-y-2">
                  <label class="text-sm font-semibold">电子邮箱</label>
                  <input class="w-full px-4 py-2.5 rounded-xl border dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 focus:ring-2 focus:ring-indigo-500 outline-none transition-all" type="email" value="felix.z@example.com" />
                </div>
              </div>
              <div class="pt-6 border-t dark:border-slate-800 space-y-4">
                <h3 class="font-bold">修改密码</h3>
                <div class="grid grid-cols-1 gap-4">
                  <input
                    v-model="pwdCurrent"
                    class="w-full px-4 py-2.5 rounded-xl border dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 outline-none"
                    placeholder="当前密码"
                    type="password"
                    autocomplete="current-password"
                  />
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <input
                      v-model="pwdNew"
                      class="w-full px-4 py-2.5 rounded-xl border dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 outline-none"
                      placeholder="新密码"
                      type="password"
                      autocomplete="new-password"
                    />
                    <input
                      v-model="pwdNew2"
                      class="w-full px-4 py-2.5 rounded-xl border dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 outline-none"
                      placeholder="确认新密码"
                      type="password"
                      autocomplete="new-password"
                    />
                  </div>
                </div>
                <p v-if="pwdMsg" class="text-sm text-rose-500">{{ pwdMsg }}</p>
                <button
                  class="px-6 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-bold hover:bg-indigo-700 disabled:opacity-60"
                  type="button"
                  :disabled="pwdSubmitting"
                  @click="submitPasswordChange"
                >
                  {{ pwdSubmitting ? "提交中…" : "更新密码" }}
                </button>
              </div>
              <div class="flex justify-end pt-4">
                <button
                  class="px-8 py-2.5 text-white font-bold rounded-xl transition-all shadow-lg shadow-indigo-200 dark:shadow-none"
                  :class="saveState === 'done' ? 'bg-green-600' : 'bg-indigo-600 hover:bg-indigo-700'"
                  :disabled="saveState === 'saving'"
                  type="submit"
                >
                  {{ saveState === "saving" ? "正在保存..." : saveState === "done" ? "已保存" : "保存更改" }}
                </button>
              </div>
            </form>
          </section>

          <section v-else-if="activeTab === 'preferences'" class="space-y-6">
            <h2 class="text-2xl font-bold">偏好设置</h2>
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h4 class="font-semibold">默认目标语言</h4>
                <p class="text-sm text-slate-500">上传新文档时默认选择的翻译语言</p>
              </div>
              <select class="w-full md:w-48 px-4 py-2 rounded-xl border dark:border-slate-800 bg-white dark:bg-slate-900 outline-none">
                <option>简体中文</option>
                <option>English</option>
              </select>
            </div>
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h4 class="font-semibold">界面语言</h4>
                <p class="text-sm text-slate-500">系统界面的显示语言</p>
              </div>
              <select class="w-full md:w-48 px-4 py-2 rounded-xl border dark:border-slate-800 bg-white dark:bg-slate-900 outline-none">
                <option>简体中文</option>
                <option>English</option>
              </select>
            </div>
            <div class="flex items-center justify-between py-2">
              <div>
                <h4 class="font-semibold">自动保存翻译历史</h4>
                <p class="text-sm text-slate-500">关闭后将不记录文档翻译历史</p>
              </div>
              <button class="relative inline-block w-11 h-6 rounded-full transition-colors" :class="autoSaveHistory ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-slate-700'" type="button" @click="autoSaveHistory = !autoSaveHistory">
                <span class="absolute top-[2px] h-5 w-5 rounded-full bg-white transition-all" :class="autoSaveHistory ? 'left-[22px]' : 'left-[2px]'"></span>
              </button>
            </div>
            <div class="pt-6 border-t dark:border-slate-800 space-y-4">
              <h4 class="font-semibold">快捷键偏好</h4>
              <div class="grid grid-cols-1 gap-2">
                <div class="flex justify-between items-center text-sm p-3 rounded-lg bg-slate-100 dark:bg-slate-800">
                  <span>快速上传文档</span>
                  <kbd class="px-2 py-1 bg-white dark:bg-slate-900 border dark:border-slate-700 rounded shadow-sm font-sans">Alt + U</kbd>
                </div>
                <div class="flex justify-between items-center text-sm p-3 rounded-lg bg-slate-100 dark:bg-slate-800">
                  <span>搜索翻译历史</span>
                  <kbd class="px-2 py-1 bg-white dark:bg-slate-900 border dark:border-slate-700 rounded shadow-sm font-sans">Cmd + F</kbd>
                </div>
              </div>
            </div>
          </section>

          <section v-else-if="activeTab === 'appearance'" class="space-y-8">
            <h2 class="text-2xl font-bold">主题与界面</h2>
            <div>
              <h4 class="font-semibold mb-4">外观模式</h4>
              <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                <button class="p-4 rounded-2xl border-2 border-indigo-600 bg-white text-slate-900 flex flex-col items-center gap-2" type="button" @click="$emit('toggle-theme')">
                  <Icon class="text-2xl" icon="ph:sun-bold" />
                  <span class="text-sm font-bold">浅色模式</span>
                </button>
                <button class="p-4 rounded-2xl border-2 border-slate-200 dark:border-slate-800 bg-slate-900 text-white flex flex-col items-center gap-2" type="button" @click="$emit('toggle-theme')">
                  <Icon class="text-2xl" icon="ph:moon-bold" />
                  <span class="text-sm font-bold">深色模式</span>
                </button>
              </div>
            </div>
            <div>
              <h4 class="font-semibold mb-4">主题色</h4>
              <div class="flex flex-wrap gap-4">
                <button class="w-8 h-8 rounded-full bg-indigo-600 ring-2 ring-offset-2 ring-indigo-600" type="button"></button>
                <button class="w-8 h-8 rounded-full bg-blue-500" type="button"></button>
                <button class="w-8 h-8 rounded-full bg-emerald-500" type="button"></button>
                <button class="w-8 h-8 rounded-full bg-purple-500" type="button"></button>
                <button class="w-8 h-8 rounded-full bg-rose-500" type="button"></button>
              </div>
            </div>
            <div>
              <h4 class="font-semibold mb-4">界面密度</h4>
              <div class="space-y-3">
                <label class="flex items-center gap-3 cursor-pointer p-4 rounded-xl border dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <input class="w-4 h-4 text-indigo-600" name="density" type="radio" />
                  <div>
                    <p class="font-medium">紧凑 (Compact)</p>
                    <p class="text-xs text-slate-500">最大化内容显示，减少间距</p>
                  </div>
                </label>
                <label class="flex items-center gap-3 cursor-pointer p-4 rounded-xl border-2 border-indigo-600 bg-indigo-50/50 dark:bg-indigo-900/10">
                  <input checked class="w-4 h-4 text-indigo-600" name="density" type="radio" />
                  <div>
                    <p class="font-medium text-indigo-600">舒适 (Comfortable)</p>
                    <p class="text-xs text-slate-500">默认比例，兼顾平衡</p>
                  </div>
                </label>
                <label class="flex items-center gap-3 cursor-pointer p-4 rounded-xl border dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <input class="w-4 h-4 text-indigo-600" name="density" type="radio" />
                  <div>
                    <p class="font-medium">宽松 (Relaxed)</p>
                    <p class="text-xs text-slate-500">更大的边距和字体，缓解眼部疲劳</p>
                  </div>
                </label>
              </div>
            </div>
          </section>

          <section v-else-if="activeTab === 'notifications'" class="space-y-6">
            <h2 class="text-2xl font-bold">通知设置</h2>
            <div class="flex items-center justify-between">
              <div>
                <h4 class="font-semibold">邮件通知</h4>
                <p class="text-sm text-slate-500">接收每月翻译报告、账户安全变动提醒</p>
              </div>
              <button class="relative inline-block w-11 h-6 rounded-full transition-colors" :class="mailNotice ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-slate-700'" type="button" @click="mailNotice = !mailNotice">
                <span class="absolute top-[2px] h-5 w-5 rounded-full bg-white transition-all" :class="mailNotice ? 'left-[22px]' : 'left-[2px]'"></span>
              </button>
            </div>
            <div class="flex items-center justify-between">
              <div>
                <h4 class="font-semibold">桌面通知</h4>
                <p class="text-sm text-slate-500">在浏览器后台运行时接收推送</p>
              </div>
              <button class="relative inline-block w-11 h-6 rounded-full transition-colors" :class="desktopNotice ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-slate-700'" type="button" @click="desktopNotice = !desktopNotice">
                <span class="absolute top-[2px] h-5 w-5 rounded-full bg-white transition-all" :class="desktopNotice ? 'left-[22px]' : 'left-[2px]'"></span>
              </button>
            </div>
            <div class="flex items-center justify-between">
              <div>
                <h4 class="font-semibold">处理完成提醒</h4>
                <p class="text-sm text-slate-500">当长文档翻译完成时通过弹窗提醒</p>
              </div>
              <button class="relative inline-block w-11 h-6 rounded-full transition-colors" :class="doneNotice ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-slate-700'" type="button" @click="doneNotice = !doneNotice">
                <span class="absolute top-[2px] h-5 w-5 rounded-full bg-white transition-all" :class="doneNotice ? 'left-[22px]' : 'left-[2px]'"></span>
              </button>
            </div>
          </section>

          <section v-else-if="activeTab === 'upload'" class="space-y-6">
            <h2 class="text-2xl font-bold">上传与输出</h2>
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h4 class="font-semibold">文件大小限制</h4>
                <p class="text-sm text-slate-500">单次上传的最大限制 (您的计划支持最高 100MB)</p>
              </div>
              <select class="w-full md:w-48 px-4 py-2 rounded-xl border dark:border-slate-800 bg-white dark:bg-slate-900 outline-none">
                <option>20 MB (推荐)</option>
                <option>50 MB</option>
                <option>100 MB</option>
              </select>
            </div>
            <div class="flex items-center justify-between">
              <div>
                <h4 class="font-semibold">自动导入</h4>
                <p class="text-sm text-slate-500">自动从云端硬盘同步新的 PDF 文档</p>
              </div>
              <button class="px-4 py-2 bg-slate-100 dark:bg-slate-800 rounded-lg text-sm font-medium hover:bg-slate-200 transition-colors" type="button">
                绑定 Google Drive
              </button>
            </div>
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h4 class="font-semibold">默认输出格式</h4>
                <p class="text-sm text-slate-500">翻译完成后默认生成的下载格式</p>
              </div>
              <div class="flex gap-2">
                <button class="px-3 py-1.5 rounded-lg border-2 border-indigo-600 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 text-xs font-bold" type="button">PDF</button>
                <button class="px-3 py-1.5 rounded-lg border dark:border-slate-800 text-slate-500 text-xs font-bold" type="button">DOCX</button>
                <button class="px-3 py-1.5 rounded-lg border dark:border-slate-800 text-slate-500 text-xs font-bold" type="button">TXT</button>
              </div>
            </div>
          </section>

          <section v-else class="space-y-8">
            <h2 class="text-2xl font-bold">隐私与安全</h2>
            <div>
              <h4 class="font-semibold mb-2">数据保留设置</h4>
              <p class="text-sm text-slate-500 mb-4">设置翻译完成后文档在云端存储的时间</p>
              <select class="w-full px-4 py-2.5 rounded-xl border dark:border-slate-800 bg-white dark:bg-slate-900 outline-none">
                <option>立即删除</option>
                <option>24 小时后删除</option>
                <option selected>7 天后自动删除</option>
                <option>30 天后自动删除</option>
                <option>永久保留</option>
              </select>
            </div>
            <div class="pt-6 border-t dark:border-slate-800">
              <h4 class="font-semibold mb-4">API 密钥管理</h4>
              <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-dashed dark:border-slate-700">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-xs font-mono text-slate-400">sk-trans-************************88a</span>
                  <button class="text-indigo-600 text-sm font-medium" type="button">查看</button>
                </div>
                <p class="text-xs text-slate-500">API 密钥用于第三方应用调用翻译接口。请妥善保管。</p>
              </div>
              <button class="mt-4 text-sm font-bold text-indigo-600 flex items-center gap-1" type="button">
                <Icon icon="ph:plus-bold" />
                创建新密钥
              </button>
            </div>
            <div class="pt-10 border-t dark:border-slate-800">
              <h4 class="text-red-500 font-bold mb-2">危险区域</h4>
              <p class="text-sm text-slate-500 mb-4">一旦删除账户，所有数据将无法恢复。请谨慎操作。</p>
              <button class="px-6 py-2 border-2 border-red-200 dark:border-red-900/30 text-red-500 font-bold rounded-xl hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors" type="button">
                注销账户
              </button>
            </div>
          </section>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Icon } from "@iconify/vue";
import * as authApi from "./api/auth";

const props = defineProps<{
  serviceTime: string;
  avatarUrl?: string;
}>();

const emit = defineEmits<{
  (e: "toggle-theme"): void;
  (e: "password-changed"): void;
}>();

type SettingsTab = "account" | "preferences" | "appearance" | "notifications" | "upload" | "privacy";

const tabs: Array<{ id: SettingsTab; label: string; icon: string }> = [
  { id: "account", label: "账户设置", icon: "ph:user-circle-bold" },
  { id: "preferences", label: "偏好设置", icon: "ph:gear-six-bold" },
  { id: "appearance", label: "主题与界面", icon: "ph:palette-bold" },
  { id: "notifications", label: "通知设置", icon: "ph:bell-bold" },
  { id: "upload", label: "上传与输出", icon: "ph:cloud-arrow-up-bold" },
  { id: "privacy", label: "隐私与安全", icon: "ph:shield-check-bold" },
];

const activeTab = ref<SettingsTab>("account");
const avatarUrl = ref(props.avatarUrl || "https://api.dicebear.com/7.x/avataaars/svg?seed=Felix");
const pwdCurrent = ref("");
const pwdNew = ref("");
const pwdNew2 = ref("");
const pwdMsg = ref("");
const pwdSubmitting = ref(false);
const saveState = ref<"idle" | "saving" | "done">("idle");
const autoSaveHistory = ref(true);
const mailNotice = ref(true);
const desktopNotice = ref(false);
const doneNotice = ref(true);

function previewAvatar(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (ev) => {
    avatarUrl.value = String(ev.target?.result || avatarUrl.value);
  };
  reader.readAsDataURL(file);
}

function saveSettings() {
  saveState.value = "saving";
  window.setTimeout(() => {
    saveState.value = "done";
    window.setTimeout(() => {
      saveState.value = "idle";
    }, 1200);
  }, 700);
}

async function submitPasswordChange() {
  pwdMsg.value = "";
  if (!sessionStorage.getItem("axiomflow:accessToken")) {
    pwdMsg.value = "请先登录后再修改密码";
    return;
  }
  if (pwdNew.value.length < 8 || !/[A-Za-z]/.test(pwdNew.value) || !/\d/.test(pwdNew.value)) {
    pwdMsg.value = "新密码至少 8 位，且包含英文和数字";
    return;
  }
  if (pwdNew.value !== pwdNew2.value) {
    pwdMsg.value = "两次输入的新密码不一致";
    return;
  }
  pwdSubmitting.value = true;
  try {
    await authApi.changePassword({ current_password: pwdCurrent.value, new_password: pwdNew.value });
    pwdCurrent.value = "";
    pwdNew.value = "";
    pwdNew2.value = "";
    emit("password-changed");
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
    if (detail === "invalid_current_password") pwdMsg.value = "当前密码不正确";
    else pwdMsg.value = "修改失败，请稍后重试";
  } finally {
    pwdSubmitting.value = false;
  }
}
</script>
