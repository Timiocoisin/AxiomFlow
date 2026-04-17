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
              <img
                alt="Large Avatar"
                class="w-32 h-32 rounded-3xl border-4 border-white dark:border-slate-800 shadow-xl object-cover cursor-pointer"
                :src="avatarUrl"
                @click="openAvatarPicker"
              />
              <input
                ref="avatarInputRef"
                class="hidden"
                type="file"
                accept="image/png,image/jpeg,image/webp,image/gif"
                @change="onAvatarFileChange"
              />
              <button
                class="absolute -bottom-2 -right-2 w-10 h-10 bg-indigo-600 text-white rounded-xl flex items-center justify-center shadow-lg hover:scale-110 transition-transform"
                type="button"
                :disabled="avatarUploading"
                @click="openAvatarPicker"
              >
                <Icon icon="ph:camera-bold" />
              </button>
            </div>
            <div class="text-center sm:text-left space-y-1">
              <h3 class="text-xl font-bold">{{ profileUsername || "未设置用户名" }}</h3>
              <p class="text-slate-500 text-sm">注册时间：{{ registerDate }}</p>
              <p v-if="avatarMsg" class="text-sm" :class="avatarMsgType === 'error' ? 'text-rose-500' : 'text-emerald-500'">
                {{ avatarMsg }}
              </p>
              <div class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 text-xs font-bold mt-2">
                <Icon icon="ph:crown-bold" />
                专业版用户
              </div>
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
              <label class="text-sm font-semibold text-slate-500 ml-1">用户名</label>
              <input
                class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                type="text"
                :value="profileUsername"
                readonly
              />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-semibold text-slate-500 ml-1">电子邮箱</label>
              <input
                class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                type="email"
                :value="profileEmail"
                readonly
              />
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'stats'" class="space-y-8">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="glass rounded-3xl p-6 border-l-4 border-l-indigo-600">
              <p class="text-slate-500 text-sm font-medium mb-1">已翻译文档</p>
              <h3 class="text-3xl font-bold">{{ formatNumber(translatedDocuments) }}</h3>
              <p class="text-xs mt-2 flex items-center gap-1" :class="monthDeltaPct >= 0 ? 'text-green-500' : 'text-rose-500'">
                <Icon icon="ph:trend-up-bold" /> 比上月 {{ monthDeltaPct >= 0 ? "+" : "" }}{{ monthDeltaPct }}%
              </p>
            </div>
            <div class="glass rounded-3xl p-6 border-l-4 border-l-purple-600">
              <p class="text-slate-500 text-sm font-medium mb-1">总翻译字数</p>
              <h3 class="text-3xl font-bold">{{ formatNumber(translatedWords) }}</h3>
              <p class="text-xs text-slate-500 mt-2">约节省 {{ formatNumber(hoursSaved) }} 小时工作量</p>
            </div>
            <div class="glass rounded-3xl p-6 border-l-4 border-l-orange-600">
              <p class="text-slate-500 text-sm font-medium mb-1">翻译积分余额</p>
              <h3 class="text-3xl font-bold">{{ formatNumber(creditsBalance) }}</h3>
              <p class="text-xs text-indigo-600 mt-2 font-medium cursor-pointer hover:underline">立即充值 →</p>
            </div>
          </div>
          <div class="glass rounded-3xl p-8">
            <h2 class="text-xl font-bold mb-6">活跃度分析</h2>
            <div ref="activityChartRef" class="w-full h-80"></div>
          </div>

          <div class="glass rounded-3xl p-8">
            <h2 class="text-xl font-bold mb-6">最近活动</h2>
            <div v-if="statsLoading" class="text-sm text-slate-500">加载中...</div>
            <div v-else-if="recentActivities.length === 0" class="text-sm text-slate-500">暂无活动</div>
            <div v-else class="space-y-6">
              <div v-for="item in recentActivities" :key="`${item.time}-${item.title}`" class="flex gap-4">
                <div class="w-10 h-10 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center text-indigo-600 flex-shrink-0">
                  <Icon class="text-xl" icon="ph:activity-bold" />
                </div>
                <div>
                  <p class="text-sm font-bold">{{ item.title }}</p>
                  <p class="text-xs text-slate-500">{{ formatTimeText(item.time) }} · {{ activityStatusLabel(item.status) }} · {{ item.ip || "-" }}</p>
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
                <tbody v-if="displayLoginHistory.length > 0" class="divide-y dark:divide-slate-800">
                  <tr v-for="row in displayLoginHistory" :key="`${row.time}-${row.device}-${row.ip}`">
                    <td class="py-4 font-medium" :title="row.device">{{ row.device }}</td>
                    <td class="py-4 text-slate-500">{{ row.ip }}</td>
                    <td class="py-4 text-slate-500">{{ formatTimeText(row.time) }}</td>
                    <td class="py-4">
                      <span :class="row.status.startsWith('online') ? 'text-green-500 font-bold' : 'text-slate-500'">
                        {{
                          row.status === "online_current"
                            ? "• 当前"
                            : row.status === "online"
                              ? "• 在线"
                              : "已过期"
                        }}
                      </span>
                    </td>
                  </tr>
                </tbody>
                <tbody v-else>
                  <tr>
                    <td class="py-4 text-slate-500" colspan="4">暂无登录历史</td>
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
                @click="toggleBrowserNotify"
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
            <p v-if="notifyMsg" class="text-sm mb-4" :class="notifyMsgType === 'error' ? 'text-rose-500' : 'text-emerald-500'">
              {{ notifyMsg }}
            </p>
            <p v-else-if="notifyUpdatedAt" class="text-xs text-slate-500 mb-4">
              上次更新：{{ formatTimeText(notifyUpdatedAt) }}
            </p>
            <button
              class="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-lg shadow-indigo-600/20 active:scale-95 disabled:opacity-60"
              type="button"
              :disabled="notifySaving"
              @click="saveNotificationPreferences"
            >
              {{ notifySaving ? "保存中…" : "保存设置" }}
            </button>
          </div>
        </div>

        <div v-else class="space-y-8">
          <div class="glass rounded-3xl p-8">
            <h2 class="text-xl font-bold mb-4">导出个人数据</h2>
            <p class="text-slate-500 text-sm mb-6">您可以下载包含所有个人信息、翻译记录和设置偏好的数据包（JSON 格式）。</p>
            <p v-if="exportMsg" class="text-sm mb-4" :class="exportMsgType === 'error' ? 'text-rose-500' : 'text-emerald-500'">
              {{ exportMsg }}
            </p>
            <button
              class="flex items-center gap-2 px-6 py-3 border-2 border-slate-200 dark:border-slate-800 rounded-xl font-bold hover:bg-slate-50 dark:hover:bg-slate-800 transition-all disabled:opacity-60"
              type="button"
              :disabled="exportingData"
              @click="handleExportData"
            >
              <Icon icon="ph:download-simple-bold" />
              {{ exportingData ? "导出中…" : "申请导出数据" }}
            </button>
          </div>
          <div class="bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30 rounded-3xl p-8">
            <h2 class="text-xl font-bold text-red-600 mb-4 flex items-center gap-2">
              <Icon icon="ph:warning-circle-bold" />
              危险区域
            </h2>
            <p class="text-red-700/70 dark:text-red-400/70 text-sm mb-6">一旦注销账户，所有翻译文档和积分将永久丢失且无法找回。请谨慎操作。</p>
            <div class="space-y-3 max-w-md">
              <input
                v-model="deletePassword"
                class="w-full bg-white/90 dark:bg-slate-900/40 border border-red-200 dark:border-red-900/40 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500/40 transition-all"
                type="password"
                autocomplete="current-password"
                placeholder="输入当前密码"
              />
              <input
                v-model="deleteConfirmText"
                class="w-full bg-white/90 dark:bg-slate-900/40 border border-red-200 dark:border-red-900/40 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500/40 transition-all"
                type="text"
                placeholder="输入 DELETE 进行二次确认"
              />
              <p v-if="deleteMsg" class="text-sm" :class="deleteMsgType === 'error' ? 'text-rose-500' : 'text-emerald-500'">
                {{ deleteMsg }}
              </p>
              <button
                class="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-xl font-bold transition-all shadow-lg shadow-red-600/20 disabled:opacity-60"
                type="button"
                :disabled="deletingAccount"
                @click="openDeleteConfirm"
              >
                {{ deletingAccount ? "处理中…" : "永久注销账户" }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>

  <div
    v-if="showDeleteConfirmModal"
    class="fixed inset-0 z-[220] flex items-center justify-center px-4"
    @click.self="closeDeleteConfirm"
  >
    <div class="absolute inset-0 bg-slate-950/60 backdrop-blur-sm"></div>
    <div class="relative w-full max-w-md rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6">
      <h3 class="text-lg font-bold text-red-600 mb-2">确认永久注销账户</h3>
      <p class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed mb-5">
        注销后将永久删除你的账户数据，且无法恢复。请确认你已完成数据导出。
      </p>
      <div class="flex justify-end gap-3">
        <button
          class="px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
          type="button"
          @click="closeDeleteConfirm"
        >
          取消
        </button>
        <button
          class="px-4 py-2 rounded-xl bg-red-600 text-white font-semibold hover:bg-red-700 disabled:opacity-60"
          type="button"
          :disabled="deletingAccount"
          @click="confirmDeleteAccount"
        >
          {{ deletingAccount ? "处理中…" : "确认注销" }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { Icon } from "@iconify/vue";
import * as echarts from "echarts";
import * as authApi from "./api/auth";

const emit = defineEmits<{ (e: "password-changed"): void; (e: "avatar-updated", value: string): void; (e: "account-deleted"): void }>();
const props = defineProps<{ avatarUrl?: string }>();

type TabId = "basic" | "stats" | "security" | "notifications" | "actions";

const activeTab = ref<TabId>("basic");
const avatarUrl = computed(() => props.avatarUrl || "https://api.dicebear.com/7.x/avataaars/svg?seed=Felix");
const secCurrent = ref("");
const secNew = ref("");
const secNew2 = ref("");
const secMsg = ref("");
const secSubmitting = ref(false);
const notifyEmail = ref(true);
const notifyBrowser = ref(false);
const notifyMarketing = ref(false);
const notifySaving = ref(false);
const notifyMsg = ref("");
const notifyMsgType = ref<"error" | "success">("success");
const notifyUpdatedAt = ref("");
const exportingData = ref(false);
const exportMsg = ref("");
const exportMsgType = ref<"error" | "success">("success");
const deletingAccount = ref(false);
const deletePassword = ref("");
const deleteConfirmText = ref("");
const deleteMsg = ref("");
const deleteMsgType = ref<"error" | "success">("success");
const showDeleteConfirmModal = ref(false);
const activityChartRef = ref<HTMLElement | null>(null);
const avatarInputRef = ref<HTMLInputElement | null>(null);
const avatarUploading = ref(false);
const avatarMsg = ref("");
const avatarMsgType = ref<"error" | "success">("success");
const profileUsername = ref("");
const profileEmail = ref("");
const statsLoading = ref(false);
const translatedDocuments = ref(0);
const translatedWords = ref(0);
const creditsBalance = ref(0);
const monthDeltaPct = ref(0);
const hoursSaved = ref(0);
const activityChartData = ref<Array<{ date: string; count: number }>>([]);
const recentActivities = ref<Array<{ title: string; time: string; status: string; ip: string }>>([]);
const loginHistory = ref<Array<{ device: string; ip: string; time: string; status: string }>>([]);
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

function normalizeDeviceLabel(raw: string): string {
  const t = (raw || "").toLowerCase();
  if (!t) return "Unknown device";
  const browser = t.includes("edg/")
    ? "Edge"
    : t.includes("chrome/")
      ? "Chrome"
      : t.includes("firefox/")
        ? "Firefox"
        : t.includes("safari/") && !t.includes("chrome/")
          ? "Safari"
          : "Browser";
  const os = t.includes("windows")
    ? "Windows"
    : t.includes("mac os x") || t.includes("macintosh")
      ? "macOS"
      : t.includes("android")
        ? "Android"
        : t.includes("iphone") || t.includes("ipad") || t.includes("ios")
          ? "iOS"
          : t.includes("linux")
            ? "Linux"
            : "Unknown OS";
  return `${browser} on ${os}`;
}

const displayLoginHistory = computed(() => {
  const rows = [...loginHistory.value].sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime());
  const merged = new Map<string, { device: string; ip: string; time: string; status: string }>();
  for (const row of rows) {
    const device = normalizeDeviceLabel(row.device);
    const ip = row.ip || "-";
    const key = `${device}|${ip}`;
    if (!merged.has(key)) {
      merged.set(key, { ...row, device, ip });
    }
  }
  const compact = Array.from(merged.values()).slice(0, 5);
  let markedCurrent = false;
  return compact.map((row) => {
    if (!markedCurrent && row.status.startsWith("online")) {
      markedCurrent = true;
      return { ...row, status: "online_current" };
    }
    if (row.status === "online_current") return { ...row, status: "online" };
    return row;
  });
});

function openAvatarPicker() {
  if (avatarUploading.value) return;
  avatarInputRef.value?.click();
}

async function onAvatarFileChange(ev: Event) {
  const input = ev.target as HTMLInputElement | null;
  const file = input?.files?.[0];
  if (!file) return;
  avatarMsg.value = "";
  if (!file.type.startsWith("image/")) {
    avatarMsgType.value = "error";
    avatarMsg.value = "请选择图片文件";
    input.value = "";
    return;
  }
  const maxBytes = 1024 * 1024;
  if (file.size > maxBytes) {
    avatarMsgType.value = "error";
    avatarMsg.value = "图片不能超过 1MB";
    input.value = "";
    return;
  }
  avatarUploading.value = true;
  try {
    const dataUrl = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ""));
      reader.onerror = () => reject(new Error("read_failed"));
      reader.readAsDataURL(file);
    });
    await authApi.updateAvatar({ avatar_url: dataUrl });
    try {
      const me = await authApi.getMe();
      emit("avatar-updated", String(me?.avatar_url || dataUrl));
    } catch {
      emit("avatar-updated", dataUrl);
    }
    avatarMsgType.value = "success";
    avatarMsg.value = "头像已更新";
  } catch {
    avatarMsgType.value = "error";
    avatarMsg.value = "头像更新失败，请稍后重试";
  } finally {
    avatarUploading.value = false;
    input.value = "";
  }
}

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

async function loadProfileMe() {
  try {
    const me = await authApi.getMe();
    profileUsername.value = String(me?.username || "");
    profileEmail.value = String(me?.email || "");
  } catch {
    profileUsername.value = "";
    profileEmail.value = "";
  }
}

function formatNumber(v: number): string {
  return new Intl.NumberFormat("zh-CN").format(Math.max(0, Number(v) || 0));
}

function formatTimeText(v: string): string {
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return "-";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function activityStatusLabel(status: string): string {
  if (status === "online") return "在线";
  if (status === "expired") return "已过期";
  return "信息";
}

async function loadProfileStats() {
  statsLoading.value = true;
  try {
    const stats = await authApi.getProfileStats();
    translatedDocuments.value = Number(stats?.metrics?.translated_documents || 0);
    translatedWords.value = Number(stats?.metrics?.translated_words || 0);
    creditsBalance.value = Number(stats?.metrics?.credits_balance || 0);
    monthDeltaPct.value = Number(stats?.metrics?.month_delta_pct || 0);
    hoursSaved.value = Number(stats?.metrics?.hours_saved || 0);
    activityChartData.value = Array.isArray(stats?.activity_chart) ? stats.activity_chart : [];
    recentActivities.value = Array.isArray(stats?.recent_activities) ? stats.recent_activities : [];
    loginHistory.value = Array.isArray(stats?.login_history) ? stats.login_history : [];
  } catch {
    translatedDocuments.value = 0;
    translatedWords.value = 0;
    creditsBalance.value = 0;
    monthDeltaPct.value = 0;
    hoursSaved.value = 0;
    activityChartData.value = [];
    recentActivities.value = [];
    loginHistory.value = [];
  } finally {
    statsLoading.value = false;
  }
}

async function loadNotificationPreferences() {
  notifyMsg.value = "";
  try {
    const pref = await authApi.getNotificationPreferences();
    notifyEmail.value = Boolean(pref.notify_email);
    notifyBrowser.value = Boolean(pref.notify_browser);
    if ("Notification" in window && Notification.permission === "denied") {
      notifyBrowser.value = false;
    }
    notifyMarketing.value = Boolean(pref.notify_marketing);
    notifyUpdatedAt.value = String(pref.updated_at || "");
  } catch {
    notifyMsgType.value = "error";
    notifyMsg.value = "通知设置加载失败";
  }
}

async function toggleBrowserNotify() {
  notifyMsg.value = "";
  if (!notifyBrowser.value) {
    if (!("Notification" in window)) {
      notifyMsgType.value = "error";
      notifyMsg.value = "当前浏览器不支持推送通知";
      return;
    }
    if (Notification.permission === "default") {
      const granted = await Notification.requestPermission();
      if (granted !== "granted") {
        notifyMsgType.value = "error";
        notifyMsg.value = "浏览器通知权限未开启";
        notifyBrowser.value = false;
        return;
      }
    }
    if (Notification.permission !== "granted") {
      notifyMsgType.value = "error";
      notifyMsg.value = "浏览器通知权限未开启";
      notifyBrowser.value = false;
      return;
    }
    notifyBrowser.value = true;
    return;
  }
  notifyBrowser.value = false;
}

async function saveNotificationPreferences() {
  notifySaving.value = true;
  notifyMsg.value = "";
  try {
    const pref = await authApi.updateNotificationPreferences({
      notify_email: notifyEmail.value,
      notify_browser: notifyBrowser.value,
      notify_marketing: notifyMarketing.value,
    });
    notifyUpdatedAt.value = String(pref.updated_at || "");
    notifyMsgType.value = "success";
    notifyMsg.value = "通知设置已保存";
  } catch {
    notifyMsgType.value = "error";
    notifyMsg.value = "通知设置保存失败，请稍后重试";
  } finally {
    notifySaving.value = false;
  }
}

async function handleExportData() {
  exportingData.value = true;
  exportMsg.value = "";
  try {
    const data = await authApi.exportMyData();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const d = new Date();
    const pad = (n: number) => String(n).padStart(2, "0");
    const name = `axiomflow-export-${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}.json`;
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    exportMsgType.value = "success";
    exportMsg.value = "数据导出成功";
  } catch {
    exportMsgType.value = "error";
    exportMsg.value = "数据导出失败，请稍后重试";
  } finally {
    exportingData.value = false;
  }
}

async function handleDeleteAccount() {
  deleteMsg.value = "";
  if (!deletePassword.value) {
    deleteMsgType.value = "error";
    deleteMsg.value = "请输入当前密码";
    return;
  }
  if ((deleteConfirmText.value || "").trim().toUpperCase() !== "DELETE") {
    deleteMsgType.value = "error";
    deleteMsg.value = "请输入 DELETE 进行确认";
    return;
  }
  deletingAccount.value = true;
  try {
    await authApi.deleteMyAccount({
      current_password: deletePassword.value,
      confirm_text: deleteConfirmText.value,
    });
    deleteMsgType.value = "success";
    deleteMsg.value = "账户已注销";
    showDeleteConfirmModal.value = false;
    emit("account-deleted");
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
    if (detail === "invalid_current_password") {
      deleteMsgType.value = "error";
      deleteMsg.value = "当前密码不正确";
    } else if (detail === "invalid_confirm_text") {
      deleteMsgType.value = "error";
      deleteMsg.value = "确认文本不正确";
    } else {
      deleteMsgType.value = "error";
      deleteMsg.value = "注销失败，请稍后重试";
    }
  } finally {
    deletingAccount.value = false;
  }
}

function openDeleteConfirm() {
  deleteMsg.value = "";
  showDeleteConfirmModal.value = true;
}

function closeDeleteConfirm() {
  if (deletingAccount.value) return;
  showDeleteConfirmModal.value = false;
}

function confirmDeleteAccount() {
  void handleDeleteAccount();
}

function renderActivityChart() {
  if (!activityChartRef.value) return;
  if (activityChart && activityChart.getDom() !== activityChartRef.value) {
    activityChart.dispose();
    activityChart = null;
  }
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
      data: activityChartData.value.map((x) => x.date),
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
        data: activityChartData.value.map((x) => Number(x.count || 0)),
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
  void loadProfileMe();
  void loadProfileStats();
  void loadNotificationPreferences();
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

watch(activityChartData, async () => {
  if (activeTab.value !== "stats") return;
  await nextTick();
  renderActivityChart();
  activityChart?.resize();
});
</script>
