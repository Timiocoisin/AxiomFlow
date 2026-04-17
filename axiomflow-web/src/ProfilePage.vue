<template>
  <main class="flex-grow container mx-auto px-4 py-10 max-w-5xl" id="main-content">
    <div class="flex flex-col md:flex-row gap-8">
      <aside class="hidden md:block w-64 space-y-2">
        <button
          v-for="item in tabs"
          :key="item.id"
          class="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all"
          :class="activeTab === item.id ? 'bg-white dark:bg-slate-800 shadow-md text-indigo-600' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800'"
          type="button"
          @click="activeTab = item.id"
        >
          <Icon class="text-xl" :icon="item.icon" />
          {{ item.label }}
        </button>
      </aside>

      <div class="flex-grow space-y-8">
        <div v-if="activeTab === 'basic'" class="glass rounded-3xl p-8">
          <h2 class="text-2xl font-bold mb-8">个人基本信息</h2>
          <div class="flex flex-col sm:flex-row items-center gap-8 mb-10">
            <div class="relative group">
              <img alt="Large Avatar" class="w-32 h-32 rounded-3xl border-4 border-white dark:border-slate-800 shadow-xl object-cover" :src="avatarUrl" />
              <button class="absolute -bottom-2 -right-2 w-10 h-10 bg-indigo-600 text-white rounded-xl flex items-center justify-center shadow-lg hover:scale-110 transition-transform" type="button">
                <Icon icon="ph:camera-bold" />
              </button>
            </div>
            <div class="text-center sm:text-left space-y-1">
              <h3 class="text-xl font-bold">Alex Design</h3>
              <p class="text-slate-500 text-sm">注册时间：{{ registerDate }}</p>
              <div class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 text-xs font-bold mt-2">
                <Icon icon="ph:crown-bold" />
                专业版用户
              </div>
            </div>
          </div>
          <form class="grid grid-cols-1 md:grid-cols-2 gap-6" @submit.prevent>
            <div class="space-y-2">
              <label class="text-sm font-semibold text-slate-500 ml-1">用户名</label>
              <input class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all" type="text" value="Alex Design" />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-semibold text-slate-500 ml-1">电子邮箱</label>
              <input class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all" type="email" value="alex.design@example.com" />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-semibold text-slate-500 ml-1">公司/组织</label>
              <input class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all" type="text" value="Design Lab Co." />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-semibold text-slate-500 ml-1">首选语言</label>
              <select class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all">
                <option>简体中文</option>
                <option>English</option>
              </select>
            </div>
            <div class="md:col-span-2 pt-4">
              <button class="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-lg shadow-indigo-600/20 active:scale-95" type="submit">
                保存更改
              </button>
            </div>
          </form>
        </div>

        <div v-else-if="activeTab === 'stats'" class="space-y-8">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="glass rounded-3xl p-6 border-l-4 border-l-indigo-600">
              <p class="text-slate-500 text-sm font-medium mb-1">已翻译文档</p>
              <h3 class="text-3xl font-bold">42</h3>
              <p class="text-xs text-green-500 mt-2 flex items-center gap-1">
                <Icon icon="ph:trend-up-bold" /> 比上月 +12%
              </p>
            </div>
            <div class="glass rounded-3xl p-6 border-l-4 border-l-purple-600">
              <p class="text-slate-500 text-sm font-medium mb-1">总翻译字数</p>
              <h3 class="text-3xl font-bold">125,400</h3>
              <p class="text-xs text-slate-500 mt-2">约节省 210 小时工作量</p>
            </div>
            <div class="glass rounded-3xl p-6 border-l-4 border-l-orange-600">
              <p class="text-slate-500 text-sm font-medium mb-1">翻译积分余额</p>
              <h3 class="text-3xl font-bold">8,250</h3>
              <p class="text-xs text-indigo-600 mt-2 font-medium cursor-pointer hover:underline">立即充值 →</p>
            </div>
          </div>
          <div class="glass rounded-3xl p-8">
            <h2 class="text-xl font-bold mb-6">活跃度分析</h2>
            <div ref="activityChartRef" class="w-full h-80"></div>
          </div>

          <div class="glass rounded-3xl p-8">
            <h2 class="text-xl font-bold mb-6">最近活动</h2>
            <div class="space-y-6">
              <div class="flex gap-4">
                <div class="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center text-green-600 flex-shrink-0">
                  <Icon class="text-xl" icon="ph:check-circle-bold" />
                </div>
                <div>
                  <p class="text-sm font-bold">翻译完成：2026年第一季度财务报告.pdf</p>
                  <p class="text-xs text-slate-500">2026-04-15 14:20</p>
                </div>
              </div>
              <div class="flex gap-4">
                <div class="w-10 h-10 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center text-indigo-600 flex-shrink-0">
                  <Icon class="text-xl" icon="ph:file-arrow-up-bold" />
                </div>
                <div>
                  <p class="text-sm font-bold">上传了新文档：API文档_v2.docx</p>
                  <p class="text-xs text-slate-500">2026-04-14 10:30</p>
                </div>
              </div>
              <div class="flex gap-4">
                <div class="w-10 h-10 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center text-yellow-600 flex-shrink-0">
                  <Icon class="text-xl" icon="ph:password-bold" />
                </div>
                <div>
                  <p class="text-sm font-bold">成功修改了登录密码</p>
                  <p class="text-xs text-slate-500">2026-04-10 09:15</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'security'" class="space-y-8">
          <div class="glass rounded-3xl p-8">
            <h2 class="text-2xl font-bold mb-8">修改密码</h2>
            <form class="space-y-6 max-w-md" @submit.prevent="submitPasswordChange">
              <div class="space-y-2">
                <label class="text-sm font-semibold text-slate-500 ml-1">当前密码</label>
                <input
                  v-model="secCurrent"
                  class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                  placeholder="••••••••"
                  type="password"
                  autocomplete="current-password"
                />
              </div>
              <div class="space-y-2">
                <label class="text-sm font-semibold text-slate-500 ml-1">新密码</label>
                <input
                  v-model="secNew"
                  class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                  placeholder="至少 8 位，包含数字和字母"
                  type="password"
                  autocomplete="new-password"
                />
              </div>
              <div class="space-y-2">
                <label class="text-sm font-semibold text-slate-500 ml-1">确认新密码</label>
                <input
                  v-model="secNew2"
                  class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                  placeholder="再次输入新密码"
                  type="password"
                  autocomplete="new-password"
                />
              </div>
              <p v-if="secMsg" class="text-sm text-rose-500">{{ secMsg }}</p>
              <button
                class="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-lg shadow-indigo-600/20 active:scale-95 disabled:opacity-60"
                type="submit"
                :disabled="secSubmitting"
              >
                {{ secSubmitting ? "提交中…" : "更新密码" }}
              </button>
            </form>
          </div>

          <div class="glass rounded-3xl p-8">
            <div class="flex items-center justify-between mb-6">
              <div>
                <h2 class="text-xl font-bold">两步验证 (2FA)</h2>
                <p class="text-sm text-slate-500 mt-1">通过身份验证器应用为您的账户添加额外安全保障。</p>
              </div>
              <button
                class="relative inline-block w-12 h-6 transition duration-200 ease-in-out rounded-full"
                :class="twoFactorEnabled ? 'bg-indigo-600' : 'bg-slate-200 dark:bg-slate-800'"
                type="button"
                @click="twoFactorEnabled = !twoFactorEnabled"
              >
                <span
                  class="absolute top-1 w-4 h-4 transition duration-200 ease-in-out bg-white rounded-full"
                  :class="twoFactorEnabled ? 'right-1' : 'left-1'"
                ></span>
              </button>
            </div>
            <div class="p-4 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800 rounded-2xl flex items-start gap-3">
              <Icon class="text-indigo-600 mt-0.5" icon="ph:info-bold" />
              <p class="text-sm text-indigo-900 dark:text-indigo-200">
                开启 2FA 后，在登录时除了密码外，您还需要输入动态生成的 6 位数字验证码。
              </p>
            </div>
          </div>

          <div class="glass rounded-3xl p-8">
            <h2 class="text-xl font-bold mb-6">登录历史</h2>
            <div class="overflow-x-auto">
              <table class="w-full text-left text-sm">
                <thead>
                  <tr class="text-slate-500 border-b dark:border-slate-800">
                    <th class="pb-4 font-semibold">设备/浏览器</th>
                    <th class="pb-4 font-semibold">IP 地址</th>
                    <th class="pb-4 font-semibold">时间</th>
                    <th class="pb-4 font-semibold">状态</th>
                  </tr>
                </thead>
                <tbody class="divide-y dark:divide-slate-800">
                  <tr>
                    <td class="py-4 font-medium">Chrome on Windows (当前)</td>
                    <td class="py-4 text-slate-500">124.64.18.234</td>
                    <td class="py-4 text-slate-500">2026-04-15 14:12</td>
                    <td class="py-4"><span class="text-green-500 font-bold">• 在线</span></td>
                  </tr>
                  <tr>
                    <td class="py-4 font-medium">Safari on iPhone 15 Pro</td>
                    <td class="py-4 text-slate-500">117.136.0.45</td>
                    <td class="py-4 text-slate-500">2026-04-15 08:30</td>
                    <td class="py-4 text-slate-500">已过期</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'notifications'" class="glass rounded-3xl p-8">
          <h2 class="text-2xl font-bold mb-8">通知设置</h2>
          <div class="space-y-8">
            <div class="flex items-center justify-between">
              <div>
                <p class="font-bold">邮件通知</p>
                <p class="text-sm text-slate-500">当文档翻译完成、积分变动或有重要安全提醒时发送邮件。</p>
              </div>
              <button
                class="relative inline-block w-12 h-6 transition duration-200 ease-in-out rounded-full"
                :class="notifyEmail ? 'bg-indigo-600' : 'bg-slate-200 dark:bg-slate-800'"
                type="button"
                @click="notifyEmail = !notifyEmail"
              >
                <span class="absolute top-1 w-4 h-4 transition duration-200 ease-in-out bg-white rounded-full" :class="notifyEmail ? 'right-1' : 'left-1'"></span>
              </button>
            </div>
            <div class="flex items-center justify-between">
              <div>
                <p class="font-bold">浏览器推送</p>
                <p class="text-sm text-slate-500">在浏览器通知栏实时推送翻译状态更新。</p>
              </div>
              <button
                class="relative inline-block w-12 h-6 transition duration-200 ease-in-out rounded-full"
                :class="notifyBrowser ? 'bg-indigo-600' : 'bg-slate-200 dark:bg-slate-800'"
                type="button"
                @click="notifyBrowser = !notifyBrowser"
              >
                <span class="absolute top-1 w-4 h-4 transition duration-200 ease-in-out bg-white rounded-full" :class="notifyBrowser ? 'right-1' : 'left-1'"></span>
              </button>
            </div>
            <div class="flex items-center justify-between">
              <div>
                <p class="font-bold">产品动态与市场推广</p>
                <p class="text-sm text-slate-500">接收有关新功能发布、特别优惠和活动的信息。</p>
              </div>
              <button
                class="relative inline-block w-12 h-6 transition duration-200 ease-in-out rounded-full"
                :class="notifyMarketing ? 'bg-indigo-600' : 'bg-slate-200 dark:bg-slate-800'"
                type="button"
                @click="notifyMarketing = !notifyMarketing"
              >
                <span class="absolute top-1 w-4 h-4 transition duration-200 ease-in-out bg-white rounded-full" :class="notifyMarketing ? 'right-1' : 'left-1'"></span>
              </button>
            </div>
          </div>
          <div class="mt-10 pt-10 border-t dark:border-slate-800">
            <button class="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-lg shadow-indigo-600/20 active:scale-95" type="button">
              保存设置
            </button>
          </div>
        </div>

        <div v-else class="space-y-8">
          <div class="glass rounded-3xl p-8">
            <h2 class="text-xl font-bold mb-4">导出个人数据</h2>
            <p class="text-slate-500 text-sm mb-6">您可以下载包含所有个人信息、翻译记录和设置偏好的数据包（JSON 格式）。</p>
            <button class="flex items-center gap-2 px-6 py-3 border-2 border-slate-200 dark:border-slate-800 rounded-xl font-bold hover:bg-slate-50 dark:hover:bg-slate-800 transition-all" type="button">
              <Icon icon="ph:download-simple-bold" />
              申请导出数据
            </button>
          </div>
          <div class="bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30 rounded-3xl p-8">
            <h2 class="text-xl font-bold text-red-600 mb-4 flex items-center gap-2">
              <Icon icon="ph:warning-circle-bold" />
              危险区域
            </h2>
            <p class="text-red-700/70 dark:text-red-400/70 text-sm mb-6">一旦注销账户，所有翻译文档和积分将永久丢失且无法找回。请谨慎操作。</p>
            <button class="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-xl font-bold transition-all shadow-lg shadow-red-600/20" type="button">
              永久注销账户
            </button>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { Icon } from "@iconify/vue";
import * as echarts from "echarts";
import * as authApi from "./api/auth";

const emit = defineEmits<{ (e: "password-changed"): void }>();

type TabId = "basic" | "stats" | "security" | "notifications" | "actions";

const activeTab = ref<TabId>("basic");
const avatarUrl = "https://api.dicebear.com/7.x/avataaars/svg?seed=Felix";
const secCurrent = ref("");
const secNew = ref("");
const secNew2 = ref("");
const secMsg = ref("");
const secSubmitting = ref(false);
const twoFactorEnabled = ref(false);
const notifyEmail = ref(true);
const notifyBrowser = ref(false);
const notifyMarketing = ref(false);
const activityChartRef = ref<HTMLElement | null>(null);
let activityChart: echarts.ECharts | null = null;

const tabs: Array<{ id: TabId; label: string; icon: string }> = [
  { id: "basic", label: "基本信息", icon: "ph:user-circle-bold" },
  { id: "stats", label: "数据统计", icon: "ph:chart-bar-bold" },
  { id: "security", label: "账户安全", icon: "ph:shield-check-bold" },
  { id: "notifications", label: "通知偏好", icon: "ph:bell-bold" },
  { id: "actions", label: "更多操作", icon: "ph:dots-three-circle-bold" },
];

const registerDate = computed(() => {
  const d = new Date();
  const pad = (v: number) => String(v).padStart(2, "0");
  return `${d.getFullYear()}年${pad(d.getMonth() + 1)}月${pad(d.getDate())}日`;
});

async function submitPasswordChange() {
  secMsg.value = "";
  if (!sessionStorage.getItem("axiomflow:accessToken")) {
    secMsg.value = "请先登录后再修改密码";
    return;
  }
  if (secNew.value.length < 8 || !/[A-Za-z]/.test(secNew.value) || !/\d/.test(secNew.value)) {
    secMsg.value = "新密码至少 8 位，且包含英文和数字";
    return;
  }
  if (secNew.value !== secNew2.value) {
    secMsg.value = "两次输入的新密码不一致";
    return;
  }
  secSubmitting.value = true;
  try {
    await authApi.changePassword({ current_password: secCurrent.value, new_password: secNew.value });
    secCurrent.value = "";
    secNew.value = "";
    secNew2.value = "";
    emit("password-changed");
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string }; status?: number } })?.response?.data?.detail;
    if (detail === "invalid_current_password") secMsg.value = "当前密码不正确";
    else secMsg.value = "修改失败，请稍后重试";
  } finally {
    secSubmitting.value = false;
  }
}

function renderActivityChart() {
  if (!activityChartRef.value) return;
  if (!activityChart) {
    activityChart = echarts.init(activityChartRef.value);
  }
  const isDark = document.body.classList.contains("theme-dark");
  activityChart.setOption({
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "line",
        lineStyle: {
          color: isDark ? "rgba(148,163,184,0.7)" : "rgba(100,116,139,0.45)",
          type: "dashed",
        },
      },
      backgroundColor: isDark ? "rgba(15,23,42,0.92)" : "rgba(255,255,255,0.96)",
      borderColor: isDark ? "rgba(148,163,184,0.3)" : "rgba(148,163,184,0.35)",
      borderWidth: 1,
      textStyle: {
        color: isDark ? "#e2e8f0" : "#0f172a",
      },
    },
    grid: {
      left: "5%",
      right: "3%",
      top: "8%",
      bottom: "10%",
      containLabel: true,
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: ["04-09", "04-10", "04-11", "04-12", "04-13", "04-14", "04-15"],
      axisLine: { lineStyle: { color: isDark ? "#334155" : "#e2e8f0" } },
      axisLabel: { color: isDark ? "#94a3b8" : "#94a3b8" },
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 10,
      splitNumber: 5,
      axisLabel: { color: isDark ? "#94a3b8" : "#64748b" },
      axisLine: { show: false },
      splitLine: {
        lineStyle: {
          color: isDark ? "rgba(148,163,184,0.18)" : "#e2e8f0",
        },
      },
    },
    series: [
      {
        name: "翻译文档数",
        type: "line",
        smooth: true,
        data: [3, 5, 2, 8, 4, 6, 9],
        symbol: "circle",
        symbolSize: 7,
        itemStyle: {
          color: "#6366f1",
          borderColor: "#6366f1",
          borderWidth: 2,
        },
        lineStyle: {
          color: "#6366f1",
          width: 3,
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(99, 102, 241, 0.20)" },
            { offset: 1, color: "rgba(99, 102, 241, 0)" },
          ]),
        },
      },
    ],
  });
}

function handleResize() {
  activityChart?.resize();
}

onMounted(() => {
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  activityChart?.dispose();
  activityChart = null;
});

watch(
  activeTab,
  async (tab) => {
    if (tab !== "stats") return;
    await nextTick();
    renderActivityChart();
    activityChart?.resize();
  },
  { immediate: true },
);
</script>
