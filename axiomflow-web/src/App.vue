<template>
  <AuthPage
    v-if="page === 'auth'"
    :is-dark="isDark"
    @toggle-theme="toggleTheme"
    @back="page = 'home'"
    @authed="handleAuthed"
    @verify-email="handleGoVerifyEmail"
  />
  <VerifyEmailPage
    v-else-if="page === 'verify-email'"
    :is-dark="isDark"
    :email="lastRegisterEmail"
    @toggle-theme="toggleTheme"
    @back="page = 'auth'"
    @verified="handleVerified"
  />
  <PreviewPage
    v-else-if="page === 'preview'"
    :service-time="serviceTime"
    @toggle-theme="toggleTheme"
    @back="page = 'documents'"
  />

  <template v-else>
  <div class="min-h-screen flex flex-col">
  <!-- 跳过链接 -->
  <a class="sr-only focus:not-sr-only fixed top-4 left-4 z-[200] bg-indigo-600 text-white px-4 py-2 rounded-lg" href="#main-content">跳过导航</a>
  <!-- 顶部进度条 -->
  <div class="progress-bar" id="loading-bar" :style="{ width: `${loadingBarWidth}%`, opacity: loadingBarOpacity }"></div>
  <!-- 离线提示横幅 -->
  <div class="bg-red-600 text-white text-center py-2 text-sm sticky top-0 z-[110]" id="offline-banner" :class="{ hidden: isOnline }">
    <div class="container mx-auto flex items-center justify-center gap-2">
      <Icon icon="ph:wifi-slash-bold" />
      检测到网络连接已断开，部分功能可能受限
    </div>
  </div>
  <!-- 导航栏 -->
  <nav class="sticky top-0 z-50 glass border-b dark:border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16 items-center">
        <!-- Logo -->
        <div class="flex items-center gap-2">
          <img alt="Axiomflow Logo" class="w-8 h-8 rounded-lg" src="/icons/favicon.svg">
          <span class="text-xl font-bold tracking-tight">Axiomflow</span>
        </div>
        <!-- 菜单 -->
        <div class="hidden md:flex items-center space-x-8">
          <a
            class="text-sm font-medium transition-colors"
            :class="page === 'home' ? 'text-indigo-600' : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'"
            href="#"
            @click.prevent="page = 'home'"
          >首页</a>
          <a
            class="text-sm font-medium transition-colors"
            :class="page === 'documents' ? 'text-indigo-600' : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'"
            href="#"
            @click.prevent="page = 'documents'"
          >文档</a>
        </div>
        <!-- 工具栏 -->
        <div class="flex items-center gap-3">
          <!-- 语言切换 -->
          <div class="relative group">
            <button class="h-10 inline-flex items-center gap-1 text-sm font-medium px-3 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800">
              <Icon icon="ph:globe-bold" />
              <span>中文</span>
            </button>
            <div class="absolute right-0 mt-2 w-40 bg-white dark:bg-slate-900 rounded-xl shadow-xl border dark:border-slate-800 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all p-2">
              <a class="block px-3 py-2 text-sm rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/30" href="#">中文</a>
              <a class="block px-3 py-2 text-sm rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/30" href="#">English</a>
            </div>
          </div>
          <!-- 主题切换 -->
          <button class="h-10 w-10 inline-flex items-center justify-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500" @click="toggleTheme">
            <Icon id="sun-icon" class="text-xl" icon="ph:sun-bold" :class="{ hidden: !isDark }" />
            <Icon id="moon-icon" class="text-xl" icon="ph:moon-bold" :class="{ hidden: isDark }" />
          </button>
          <button
            v-if="!isLoggedIn"
            class="h-10 inline-flex items-center justify-center px-5 rounded-xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-sm font-semibold hover:opacity-90 transition-opacity"
            @click.prevent="page = 'auth'"
          >
            登录
          </button>
          <!-- 用户菜单（登录后显示） -->
          <div v-else class="relative group">
            <button class="flex items-center gap-2 p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
              <img alt="Avatar" class="w-8 h-8 rounded-full border border-slate-200 dark:border-slate-700" src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix">
              <Icon class="text-xs text-slate-400" icon="ph:caret-down-bold" />
            </button>
            <div class="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-900 rounded-xl shadow-xl border dark:border-slate-800 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all p-2">
              <a class="flex items-center gap-2 px-3 py-2 text-sm rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800" href="#" @click.prevent="page = 'profile'">
                <Icon icon="ph:user-bold" /> 个人资料
              </a>
              <a class="flex items-center gap-2 px-3 py-2 text-sm rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800" href="#" @click.prevent="page = 'settings'">
                <Icon icon="ph:gear-six-bold" /> 账户设置
              </a>
              <div class="h-px bg-slate-100 dark:bg-slate-800 my-1"></div>
              <a class="flex items-center gap-2 px-3 py-2 text-sm rounded-lg text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30" href="#" @click.prevent="handleLogout">
                <Icon icon="ph:sign-out-bold" /> 退出登录
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>

  </nav>
  <main v-if="page === 'home'" class="hero-gradient" id="main-content">
    <!-- Hero Section -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
      <div class="grid lg:grid-cols-2 gap-16 items-center">
        <div class="space-y-8">
          <div class="relative inline-flex">
            <span class="badge-breath absolute -inset-1 rounded-full bg-indigo-500/20 dark:bg-indigo-400/20"></span>
            <span class="relative inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 text-xs font-bold uppercase tracking-wider">
              <span class="flex h-2 w-2 rounded-full bg-indigo-600"></span>
              2026年4月新版本发布
            </span>
          </div>
          <h1 class="text-5xl lg:text-7xl font-extrabold leading-tight tracking-tight">
            智能翻译<br>
            <span class="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-500">还原排版细节</span>
          </h1>
          <p class="text-lg text-slate-600 dark:text-slate-400 max-w-xl leading-relaxed">
            借助神经网络引擎，Axiomflow 不止翻译文本，还能精准还原原始 PDF 的复杂版式、字体、配色与表格结构。
          </p>
        </div>
        <!-- 上传入口 -->
          <div class="relative group">
          <div class="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-3xl blur opacity-25 group-hover:opacity-40 transition duration-1000"></div>
          <div class="upload-breath upload-surface relative border-2 border-dashed p-10 lg:p-16 rounded-3xl text-center cursor-pointer hover:border-indigo-500 transition-all" id="drop-zone" @click="openModal">
            <div class="mb-6 inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 transition-transform group-hover:scale-110">
              <Icon class="text-4xl" icon="ph:cloud-arrow-up-bold" />
            </div>
            <h3 class="text-2xl font-bold mb-2">点击或拖拽文件到此处</h3>
            <p class="text-slate-500 mb-8">支持 PDF, DOCX (最大 100MB)</p>
            <div class="flex justify-center gap-4 text-xs font-medium text-slate-400 uppercase tracking-widest">
              <span>2026年安全加密</span>
              <span>•</span>
              <span>端到端保护</span>
            </div>
          </div>
        </div>
      </div>
    </section>
    <!-- 数据展示 -->
    <section class="max-w-7xl mx-auto px-4 pb-20">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-8">
        <div class="group p-6 rounded-3xl text-center card-surface card-surface-hover hover:-translate-y-1 transition-all duration-300">
          <div class="text-3xl font-extrabold tracking-tight text-indigo-600 group-hover:text-indigo-500 transition-colors">120+</div>
          <div class="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">支持语言</div>
        </div>
        <div class="group p-6 rounded-3xl text-center card-surface card-surface-hover hover:-translate-y-1 transition-all duration-300">
          <div class="text-3xl font-extrabold tracking-tight text-indigo-600 group-hover:text-indigo-500 transition-colors">2.5s</div>
          <div class="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">平均翻译速度/页</div>
        </div>
        <div class="group p-6 rounded-3xl text-center card-surface card-surface-hover hover:-translate-y-1 transition-all duration-300">
          <div class="text-3xl font-extrabold tracking-tight text-indigo-600 group-hover:text-indigo-500 transition-colors">99.9%</div>
          <div class="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">布局还原率</div>
        </div>
        <div class="group p-6 rounded-3xl text-center card-surface card-surface-hover hover:-translate-y-1 transition-all duration-300">
          <div class="text-3xl font-extrabold tracking-tight text-indigo-600 group-hover:text-indigo-500 transition-colors">5M+</div>
          <div class="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">本月已处理文档</div>
        </div>
      </div>
    </section>
    <!-- 特性列表 -->
    <section class="py-24 section-surface">
      <div class="max-w-7xl mx-auto px-4">
        <div class="text-center mb-16 space-y-4">
          <h2 class="text-3xl md:text-5xl font-bold">为什么选择 Axiomflow</h2>
          <p class="text-slate-500 max-w-2xl mx-auto">我们不仅仅是翻译文字，更是通过 AI 视觉技术重建您的文档结构。</p>
        </div>
        <div class="grid md:grid-cols-3 gap-8">
          <!-- Feature 1 -->
          <div class="group p-8 rounded-3xl card-surface card-surface-hover hover:-translate-y-1 transition-all duration-300">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-100 to-violet-100 dark:from-indigo-500/20 dark:to-fuchsia-500/15 flex items-center justify-center text-indigo-600 mb-6 group-hover:scale-105 transition-transform">
              <Icon class="text-2xl" icon="ph:layout-bold" />
            </div>
            <h4 class="text-xl font-bold mb-3 tracking-tight">极致排版还原</h4>
            <p class="text-slate-600 dark:text-slate-400 leading-relaxed">精准识别复杂的图文混排、多级表格及复杂背景色，生成的翻译件与原件布局高度契合。</p>
          </div>
          <!-- Feature 2 -->
          <div class="group p-8 rounded-3xl card-surface card-surface-hover hover:-translate-y-1 transition-all duration-300">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-100 to-violet-100 dark:from-indigo-500/20 dark:to-fuchsia-500/15 flex items-center justify-center text-indigo-600 mb-6 group-hover:scale-105 transition-transform">
              <Icon class="text-2xl" icon="ph:shield-check-bold" />
            </div>
            <h4 class="text-xl font-bold mb-3 tracking-tight">企业级隐私保护</h4>
            <p class="text-slate-600 dark:text-slate-400 leading-relaxed">符合 2026 最新数据隐私规范，文件翻译后 24 小时自动物理擦除，保障您的机密信息。</p>
          </div>
          <!-- Feature 3 -->
          <div class="group p-8 rounded-3xl card-surface card-surface-hover hover:-translate-y-1 transition-all duration-300">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-100 to-violet-100 dark:from-indigo-500/20 dark:to-fuchsia-500/15 flex items-center justify-center text-indigo-600 mb-6 group-hover:scale-105 transition-transform">
              <Icon class="text-2xl" icon="ph:file-search-bold" />
            </div>
            <h4 class="text-xl font-bold mb-3 tracking-tight">OCR 增强识别</h4>
            <p class="text-slate-600 dark:text-slate-400 leading-relaxed">哪怕是模糊的扫描件或手写笔记，我们的 OCR 引擎也能先矫正、后翻译。</p>
          </div>
        </div>
      </div>
    </section>
  </main>
  <DocumentsPage
    v-else-if="page === 'documents'"
    :as-of-date="serviceDateCn"
    @new-translation="page = 'home'"
    @open-preview="page = 'preview'"
  />
  <ProfilePage v-else-if="page === 'profile'" />
  <SettingsPage v-else :service-time="serviceTime" @toggle-theme="toggleTheme" />
  <!-- 预览弹窗 (Mock) -->
  <div
    v-if="page === 'home'"
    class="fixed inset-0 z-[150] items-center justify-center px-4"
    id="preview-modal"
    :class="showPreview ? 'flex' : 'hidden'"
  >
    <div class="absolute inset-0 bg-slate-950/60 backdrop-blur-sm" @click="closeModal"></div>
    <div class="relative bg-white dark:bg-slate-900 w-full max-w-5xl rounded-3xl shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-300">
      <div class="p-4 border-b dark:border-slate-800 flex items-center justify-between">
        <h3 class="font-bold flex items-center gap-2">
          <Icon icon="ph:eye-bold" /> 翻译预览: 企业年度报告.pdf
        </h3>
        <button class="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg" @click="closeModal">
          <Icon icon="ph:x-bold" />
        </button>
      </div>
      <div class="grid md:grid-cols-2 h-[60vh] overflow-hidden">
        <div class="border-r dark:border-slate-800 bg-slate-100 dark:bg-slate-800 p-8 overflow-y-auto">
          <div class="text-xs font-bold text-slate-400 mb-4 uppercase tracking-wider">原文 (English)</div>
          <img alt="Original PDF content with charts" class="w-full rounded shadow-md border" src="/icons/favicon.svg">
          <div class="mt-4 p-4 bg-white dark:bg-slate-900 rounded-lg space-y-2">
            <div class="h-4 w-3/4 bg-slate-200 dark:bg-slate-800 rounded"></div>
            <div class="h-4 w-1/2 bg-slate-200 dark:bg-slate-800 rounded"></div>
          </div>
        </div>
        <div class="p-8 overflow-y-auto">
          <div class="text-xs font-bold text-indigo-500 mb-4 uppercase tracking-wider">翻译件 (中文)</div>
          <img alt="Translated PDF content with same layout" class="w-full rounded shadow-md border border-indigo-200" src="/icons/favicon.svg">
          <div class="mt-4 p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg space-y-2">
            <div class="h-4 w-3/4 bg-indigo-100 dark:bg-indigo-800/50 rounded"></div>
            <div class="h-4 w-1/2 bg-indigo-100 dark:bg-indigo-800/50 rounded"></div>
          </div>
        </div>
      </div>
      <div class="p-6 border-t dark:border-slate-800 flex justify-end gap-4">
        <button class="px-6 py-2 rounded-xl border dark:border-slate-700" @click="closeModal">取消</button>
        <button class="px-6 py-2 rounded-xl bg-indigo-600 text-white font-bold" @click="startTranslation">开始翻译并查看</button>
      </div>
    </div>
  </div>
  <!-- Toast 容器 -->
  <div v-if="page === 'home'" class="fixed bottom-8 right-8 z-[200] flex flex-col gap-3" id="toast-container">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="glass p-4 rounded-xl shadow-2xl flex items-center gap-3 animate-in slide-in-from-right-10 duration-300 min-w-[280px] border-l-4 border-l-indigo-600"
    >
      <Icon class="text-indigo-600 text-xl" icon="ph:info-bold" />
      <span class="text-sm font-medium">{{ toast.message }}</span>
      <button class="ml-auto text-slate-400 hover:text-slate-600" @click="removeToast(toast.id)">
        <Icon icon="ph:x-bold" />
      </button>
    </div>
  </div>
  <footer v-if="page === 'home'" class="section-surface pt-20 pb-10">
    <div class="max-w-7xl mx-auto px-4">
      <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-12 mb-20">
        <div class="col-span-2 lg:col-span-2">
          <div class="flex items-center gap-2 mb-6">
            <img alt="Axiomflow Logo" class="w-8 h-8 rounded-lg" src="/icons/favicon.svg">
            <span class="text-xl font-bold">Axiomflow</span>
          </div>
          <p class="text-slate-500 dark:text-slate-400 mb-8 max-w-sm">
            定义 2026 年新一代文档翻译标准。让全球协作再无边界。
          </p>
          <div class="flex gap-4">
            <a class="w-10 h-10 rounded-full border dark:border-slate-800 flex items-center justify-center text-slate-400 hover:text-indigo-600 hover:border-indigo-600 transition-all" href="#">
              <Icon class="text-xl" icon="ph:twitter-logo-bold" />
            </a>
            <a class="w-10 h-10 rounded-full border dark:border-slate-800 flex items-center justify-center text-slate-400 hover:text-indigo-600 hover:border-indigo-600 transition-all" href="#">
              <Icon class="text-xl" icon="ph:github-logo-bold" />
            </a>
            <a class="w-10 h-10 rounded-full border dark:border-slate-800 flex items-center justify-center text-slate-400 hover:text-indigo-600 hover:border-indigo-600 transition-all" href="#">
              <Icon class="text-xl" icon="ph:linkedin-logo-bold" />
            </a>
          </div>
        </div>
        <div>
          <h5 class="font-bold mb-6 uppercase text-xs tracking-widest text-slate-400">产品</h5>
          <ul class="space-y-4 text-sm font-medium text-slate-500">
            <li><a class="hover:text-indigo-600" href="#">翻译引擎</a></li>
            <li><a class="hover:text-indigo-600" href="#">批量处理</a></li>
            <li><a class="hover:text-indigo-600" href="#">API 接口</a></li>
            <li><a class="hover:text-indigo-600" href="#">浏览器插件</a></li>
          </ul>
        </div>
        <div>
          <h5 class="font-bold mb-6 uppercase text-xs tracking-widest text-slate-400">资源</h5>
          <ul class="space-y-4 text-sm font-medium text-slate-500">
            <li><a class="hover:text-indigo-600" href="#">开发文档</a></li>
            <li><a class="hover:text-indigo-600" href="#">帮助中心</a></li>
            <li><a class="hover:text-indigo-600" href="#">博客文章</a></li>
            <li><a class="hover:text-indigo-600" href="#">发布日志</a></li>
          </ul>
        </div>
        <div>
          <h5 class="font-bold mb-6 uppercase text-xs tracking-widest text-slate-400">合规</h5>
          <ul class="space-y-4 text-sm font-medium text-slate-500">
            <li><a class="hover:text-indigo-600" href="#">隐私条款</a></li>
            <li><a class="hover:text-indigo-600" href="#">服务协议</a></li>
            <li><a class="hover:text-indigo-600" href="#">Cookie 政策</a></li>
            <li><a class="hover:text-indigo-600" href="#">数据安全报告</a></li>
          </ul>
        </div>
      </div>
      <div class="pt-10 border-t dark:border-slate-800 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-slate-500">
        <p>© {{ currentYear }} Axiomflow. 保留所有权利。</p>
        <div class="flex items-center gap-6">
          <span class="flex items-center gap-2"><span class="status-light w-2.5 h-2.5 rounded-full"></span> 系统状态: 正常</span>
          <span>服务时间: {{ serviceTime }}</span>
        </div>
      </div>
    </div>
  </footer>
  <footer v-else class="mt-auto border-t dark:border-slate-800 py-8">
    <div class="max-w-7xl mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-3 text-sm text-slate-500">
      <p>© 2026 Axiomflow. 保留所有权利。</p>
      <div class="flex items-center gap-6">
        <span class="flex items-center gap-2"><span class="status-light w-2.5 h-2.5 rounded-full"></span> 系统状态: 正常</span>
        <span>服务时间: {{ serviceTime }}</span>
      </div>
    </div>
  </footer>
  </div>
</template>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { Icon } from "@iconify/vue";
import AuthPage from "./AuthPage.vue";
import DocumentsPage from "./DocumentsPage.vue";
import ProfilePage from "./ProfilePage.vue";
import SettingsPage from "./SettingsPage.vue";
import PreviewPage from "./PreviewPage.vue";
import VerifyEmailPage from "./VerifyEmailPage.vue";
import * as authApi from "./api/auth";

type ToastItem = {
  id: number;
  message: string;
};

const isDark = ref(false);
const isLoggedIn = ref(false);
const accessToken = ref<string>("");
const lastRegisterEmail = ref<string>(localStorage.getItem("axiomflow:lastRegisterEmail") || "");
const page = ref<"home" | "auth" | "documents" | "profile" | "settings" | "preview" | "verify-email">("home");
const isOnline = ref(navigator.onLine);
const showPreview = ref(false);
const loadingBarWidth = ref(0);
const loadingBarOpacity = ref(1);
const toasts = ref<ToastItem[]>([]);
const now = ref(new Date());

let toastIdSeed = 0;
let loadingTimerA: number | null = null;
let loadingTimerB: number | null = null;
let clockTimer: number | null = null;
let themeSwitchTimer: number | null = null;

const currentYear = computed(() => now.value.getFullYear());
const serviceTime = computed(() => {
  const pad = (v: number) => String(v).padStart(2, "0");
  const y = now.value.getFullYear();
  const m = pad(now.value.getMonth() + 1);
  const d = pad(now.value.getDate());
  const hh = pad(now.value.getHours());
  const mm = pad(now.value.getMinutes());
  const ss = pad(now.value.getSeconds());
  return `${y}-${m}-${d} ${hh}:${mm}:${ss}`;
});
const serviceDateCn = computed(() => {
  const pad = (v: number) => String(v).padStart(2, "0");
  const y = now.value.getFullYear();
  const m = pad(now.value.getMonth() + 1);
  const d = pad(now.value.getDate());
  return `${y}年${m}月${d}日`;
});

function updateThemeIcons() {
  const isDarkNow = document.body.classList.contains("theme-dark");
  isDark.value = isDarkNow;
}

function applyThemeClasses(dark: boolean) {
  document.documentElement.classList.toggle("dark", dark);
  document.body.classList.toggle("dark", dark);
  document.body.classList.toggle("theme-dark", dark);
  document.body.classList.toggle("theme-light", !dark);
}

function toggleTheme() {
  document.body.classList.add("theme-switching");
  if (themeSwitchTimer) window.clearTimeout(themeSwitchTimer);
  const nextDark = !document.body.classList.contains("theme-dark");
  applyThemeClasses(nextDark);
  updateThemeIcons();
  themeSwitchTimer = window.setTimeout(() => {
    document.body.classList.remove("theme-switching");
    themeSwitchTimer = null;
  }, 380);
}

function openModal() {
  showPreview.value = true;
}

function closeModal() {
  showPreview.value = false;
}

function removeToast(id: number) {
  toasts.value = toasts.value.filter((t) => t.id !== id);
}

function showToast(message: string) {
  const id = ++toastIdSeed;
  toasts.value.push({ id, message });
  window.setTimeout(() => removeToast(id), 4000);
}

function startTranslation() {
  showToast("正在初始化翻译引擎...");
  window.setTimeout(() => {
    showToast("正在上传并分析文档...");
    closeModal();
  }, 800);
}

function handleAuthed(payload: { accessToken: string }) {
  isLoggedIn.value = true;
  accessToken.value = payload.accessToken;
  sessionStorage.setItem("axiomflow:accessToken", payload.accessToken);
  page.value = "home";
  showToast("登录成功");
}

function handleVerified(payload: { accessToken: string }) {
  isLoggedIn.value = true;
  accessToken.value = payload.accessToken;
  sessionStorage.setItem("axiomflow:accessToken", payload.accessToken);
  page.value = "home";
  showToast("邮箱验证成功");
  // 清理 URL 的 token，避免带着验证参数回到首页
  window.location.hash = "#/";
}

function handleGoVerifyEmail(payload: { email: string }) {
  lastRegisterEmail.value = payload.email;
  page.value = "verify-email";
  showToast("验证邮件已发送，请查收邮箱");
}

function handleLogout() {
  authApi
    .logout()
    .catch(() => {})
    .finally(() => {
      isLoggedIn.value = false;
      accessToken.value = "";
      sessionStorage.removeItem("axiomflow:accessToken");
      page.value = "home";
      showToast("已退出登录");
    });
}

function handleOnline() {
  isOnline.value = true;
}

function handleOffline() {
  isOnline.value = false;
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === "Escape") closeModal();
}

function handleLoad() {
  loadingBarWidth.value = 30;
  loadingTimerA = window.setTimeout(() => {
    loadingBarWidth.value = 100;
  }, 300);
  loadingTimerB = window.setTimeout(() => {
    loadingBarOpacity.value = 0;
  }, 600);
}

function syncPageFromHash() {
  const h = window.location.hash || "";
  if (h.startsWith("#/verify-email")) {
    page.value = "verify-email";
    return;
  }
  if (h.startsWith("#/auth")) {
    page.value = "auth";
    return;
  }
  // 默认落回首页，避免 hash 被清理/切换后残留页面状态
  page.value = "home";
}

onMounted(() => {
  applyThemeClasses(document.documentElement.classList.contains("dark"));
  updateThemeIcons();
  window.addEventListener("load", handleLoad);
  window.addEventListener("offline", handleOffline);
  window.addEventListener("online", handleOnline);
  document.addEventListener("keydown", handleKeydown);
  syncPageFromHash();
  window.addEventListener("hashchange", syncPageFromHash);
  clockTimer = window.setInterval(() => {
    now.value = new Date();
  }, 1000);
  if (document.readyState === "complete") handleLoad();

  // Try restore login state (best-effort). Refresh is cookie-based.
  const saved = sessionStorage.getItem("axiomflow:accessToken");
  if (saved) {
    accessToken.value = saved;
    isLoggedIn.value = true;
  }
});

onBeforeUnmount(() => {
  window.removeEventListener("load", handleLoad);
  window.removeEventListener("offline", handleOffline);
  window.removeEventListener("online", handleOnline);
  document.removeEventListener("keydown", handleKeydown);
  window.removeEventListener("hashchange", syncPageFromHash);
  if (loadingTimerA) window.clearTimeout(loadingTimerA);
  if (loadingTimerB) window.clearTimeout(loadingTimerB);
  if (clockTimer) window.clearInterval(clockTimer);
  if (themeSwitchTimer) window.clearTimeout(themeSwitchTimer);
});
</script>
