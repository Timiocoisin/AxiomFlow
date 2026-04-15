<template>
  <div class="auth-shell min-h-screen flex flex-col">
    <!-- 导航栏 -->
    <nav class="sticky top-0 z-50 glass border-b border-white/10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16 items-center">
          <!-- Logo -->
          <button class="flex items-center gap-2" type="button" @click="emit('back')">
            <img alt="Axiomflow Logo" class="w-8 h-8 rounded-lg" src="/icons/favicon.svg" />
            <span class="text-xl font-bold tracking-tight text-slate-900 dark:text-white">Axiomflow</span>
          </button>
          <!-- 工具栏（占位，不跳转） -->
          <div class="flex items-center gap-3">
            <!-- 主题切换（与首页一致） -->
            <button
              class="h-10 w-10 inline-flex items-center justify-center rounded-full transition-colors text-slate-700 hover:bg-slate-900/5 dark:text-slate-200 dark:hover:bg-white/10"
              type="button"
              @click="emit('toggle-theme')"
            >
              <Icon id="sun-icon" class="text-xl" icon="ph:sun-bold" :class="{ hidden: !isDark }" />
              <Icon id="moon-icon" class="text-xl" icon="ph:moon-bold" :class="{ hidden: isDark }" />
            </button>
            <button
              class="h-10 inline-flex items-center justify-center gap-2 px-4 rounded-xl border text-sm font-semibold transition-all
              border-slate-900/10 bg-white/60 text-slate-900 hover:bg-white/80 hover:border-slate-900/15
              dark:border-white/10 dark:bg-white/5 dark:text-slate-100 dark:hover:bg-white/10"
              type="button"
              @click="emit('back')"
            >
              <Icon icon="ph:arrow-left-bold" />
              返回
            </button>
          </div>
        </div>
      </div>
    </nav>

    <div class="flex-grow flex flex-col items-center justify-center p-6">
      <div class="mb-10 text-center">
        <div class="inline-flex items-center gap-2 mb-6">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-600/30 bg-white/10 border border-white/10">
            <img alt="Axiomflow Logo" class="w-6 h-6" src="/icons/favicon.svg" />
          </div>
          <span class="text-2xl font-bold tracking-tight">Axiomflow</span>
        </div>
      </div>

      <div class="w-full max-w-md auth-card rounded-3xl p-8 lg:p-10 shadow-2xl">
        <!-- Tab 切换 -->
        <div class="flex p-1 rounded-xl mb-8 auth-tabs">
          <button
            class="flex-1 py-2 text-sm font-semibold rounded-lg shadow-sm transition-all"
            :class="mode === 'login' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'"
            type="button"
            @click="mode = 'login'"
          >
            登录
          </button>
          <button
            class="flex-1 py-2 text-sm font-semibold rounded-lg shadow-sm transition-all"
            :class="mode === 'register' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'"
            type="button"
            @click="mode = 'register'"
          >
            注册
          </button>
        </div>

        <!-- 标题区域 -->
        <div class="mb-8">
          <h2 class="text-2xl font-bold mb-2">
            {{ mode === "login" ? "欢迎回来" : "创建新账号" }}
          </h2>
          <p class="text-slate-400">
            {{
              mode === "login"
                ? "使用您的账号访问智能翻译能力"
                : "加入用户社区，开始您的智能翻译之旅"
            }}
          </p>
        </div>

        <!-- 表单 -->
        <form class="space-y-5" @submit.prevent="handleAuth">
          <div>
            <label class="block text-sm font-medium text-slate-400 mb-2">邮箱地址</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                <Icon icon="ph:envelope-simple-bold" />
              </span>
              <input
                v-model.trim="email"
                class="w-full auth-input rounded-xl py-3 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
                placeholder="name@company.com"
                required
                type="email"
              />
            </div>
          </div>

          <div v-if="mode === 'register'">
            <label class="block text-sm font-medium text-slate-400 mb-2">用户名</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                <Icon icon="ph:user-bold" />
              </span>
              <input
                v-model.trim="fullName"
                class="w-full auth-input rounded-xl py-3 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
                placeholder="请输入用户名"
                type="text"
              />
            </div>
          </div>

          <div>
            <div class="flex justify-between items-center mb-2">
              <label class="text-sm font-medium text-slate-400">密码</label>
              <a
                v-if="mode === 'login'"
                class="text-xs text-indigo-400 hover:text-indigo-300"
                href="#"
                @click.prevent
                >忘记密码?</a
              >
            </div>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                <Icon icon="ph:lock-key-bold" />
              </span>
              <input
                v-model="password"
                class="w-full auth-input rounded-xl py-3 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
                placeholder="••••••••"
                required
                type="password"
              />
            </div>
          </div>

          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <label class="text-sm font-medium text-slate-400">验证码</label>
              <span v-if="puzzleVerified" class="text-xs text-emerald-400">已验证</span>
            </div>

            <div ref="captchaWrapRef" class="relative">
              <button
                class="w-full h-12 rounded-xl border text-sm font-semibold transition-all flex items-center justify-between px-4
                border-slate-900/10 bg-white/60 text-slate-900 hover:bg-white/80 hover:border-slate-900/15
                dark:border-white/10 dark:bg-white/5 dark:text-slate-100 dark:hover:bg-white/10"
                type="button"
                :disabled="puzzleVerified"
                @click="toggleCaptchaPopover"
              >
                <span class="flex items-center gap-2">
                  <Icon :icon="puzzleVerified ? 'ph:check-circle-bold' : 'ph:shield-check-bold'" />
                  {{ puzzleVerified ? "验证成功" : "点击验证" }}
                </span>
                <span class="text-xs text-slate-500 dark:text-slate-400">
                  {{ puzzleVerified ? "已通过" : "需要完成滑动拼图" }}
                </span>
              </button>

              <div
                v-if="captchaOpen"
                class="captcha-popover absolute left-0 right-0 bottom-full mb-3 rounded-2xl border overflow-hidden"
              >
                <div class="captcha-popover-arrow"></div>
                <div class="p-4 space-y-3">
                  <div class="flex items-center justify-between">
                    <div class="text-sm font-semibold text-slate-100 dark:text-slate-100">滑动拼图验证</div>
                    <button class="text-xs text-indigo-300 hover:text-indigo-200" type="button" @click="transitionToNewPuzzle()">
                      刷新
                    </button>
                  </div>

                  <div
                    ref="puzzleAreaRef"
                    class="captcha-scene relative h-40 rounded-xl border overflow-hidden select-none"
                    :class="{
                      'captcha-scene--out': captchaScenePhase === 'out',
                      'captcha-scene--in': captchaScenePhase === 'in',
                      'captcha-scene--fail': captchaFailAnimating,
                    }"
                    :style="{
                      backgroundImage: `url(${captchaImage})`,
                      backgroundSize: `${sceneWidth}px ${sceneHeight}px`,
                      backgroundPosition: '0px 0px',
                    }"
                  >
                    <div class="absolute inset-0 captcha-scene-mask"></div>

                    <div
                      class="captcha-hole absolute border"
                      :style="{
                        left: `${targetX}px`,
                        top: `${targetY}px`,
                        width: `${pieceSize}px`,
                        height: `${pieceSize}px`,
                        clipPath: shapeClipPath,
                        opacity: puzzleVerified ? 0 : 1,
                      }"
                    ></div>

                    <div
                      class="captcha-piece absolute border shadow-md"
                      :style="{
                        left: `${pieceX}px`,
                        top: `${targetY}px`,
                        width: `${pieceSize}px`,
                        height: `${pieceSize}px`,
                        backgroundImage: `url(${captchaImage})`,
                        backgroundSize: `${sceneWidth}px ${sceneHeight}px`,
                        backgroundPosition: `${-targetX}px ${-targetY}px`,
                        clipPath: shapeClipPath,
                        opacity: pieceVisible ? 1 : 0,
                      }"
                    >
                      <div class="piece-gloss"></div>
                    </div>

                    <div class="absolute bottom-2 left-3 text-[11px] text-slate-200/90">
                      {{ puzzleVerified ? "验证通过" : "拖动滑块，把拼图移动到缺口处" }}
                    </div>
                  </div>

                  <div class="captcha-track relative h-12 rounded-xl border overflow-hidden">
                    <div class="captcha-track-fill absolute inset-y-0 left-0" :style="{ width: `${sliderX + 22}px` }"></div>
                    <div class="absolute inset-0 flex items-center justify-center text-xs font-medium text-slate-200/90 pointer-events-none">
                      {{ puzzleVerified ? "验证成功" : "向右拖动滑块完成验证" }}
                    </div>
                    <button
                      class="captcha-handle absolute top-1/2 -translate-y-1/2 h-10 w-10 rounded-lg flex items-center justify-center"
                      :style="{ left: `${sliderX}px` }"
                      type="button"
                      :disabled="puzzleVerified"
                      @pointerdown="onSliderDown"
                    >
                      <Icon icon="ph:caret-double-right-bold" />
                    </button>
                  </div>

                  <p v-if="captchaError" class="text-xs text-rose-300">{{ captchaError }}</p>
                </div>
              </div>
            </div>
          </div>

          <button class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3.5 rounded-xl transition-all shadow-lg shadow-indigo-600/20 active:scale-[0.98]" type="submit">
            继续
          </button>
        </form>

        <!-- 分割线 -->
        <div class="relative my-8">
          <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-slate-800"></div>
          </div>
          <div class="relative flex justify-center text-xs uppercase">
            <span class="auth-divider px-4 text-slate-500 tracking-widest">或者通过</span>
          </div>
        </div>

        <!-- 社交登录（占位，不跳转） -->
        <div class="grid grid-cols-2 gap-4">
          <button class="flex items-center justify-center gap-2 py-3 border border-slate-800 rounded-xl hover:bg-white/5 transition-all" type="button">
            <Icon class="text-lg" icon="logos:google-icon" />
            <span class="text-sm font-semibold">Google</span>
          </button>
          <button class="flex items-center justify-center gap-2 py-3 border border-slate-800 rounded-xl hover:bg-white/5 transition-all" type="button">
            <Icon class="text-lg" icon="logos:github-icon" />
            <span class="text-sm font-semibold">GitHub</span>
          </button>
        </div>

        <p class="mt-8 text-center text-xs text-slate-500">
          点击“继续”即表示您同意我们的
          <a class="underline hover:text-slate-300" href="#" @click.prevent>服务条款</a>
          和
          <a class="underline hover:text-slate-300" href="#" @click.prevent>隐私政策</a>
        </p>
      </div>

      <!-- 安全提示 -->
      <div class="mt-10 flex items-center gap-4 text-slate-500 text-sm">
        <span class="flex items-center gap-1.5"><Icon class="text-green-500" icon="ph:shield-check-bold" /> 256-bit SSL 加密</span>
        <span class="w-1 h-1 rounded-full bg-slate-700"></span>
        <span class="flex items-center gap-1.5"><Icon class="text-indigo-400" icon="ph:fingerprint-bold" /> 安全合规标准</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { Icon } from "@iconify/vue";

const emit = defineEmits<{
  (e: "back"): void;
  (e: "authed"): void;
  (e: "toggle-theme"): void;
}>();

defineProps<{
  isDark: boolean;
}>();

const mode = ref<"login" | "register">("login");
const email = ref("");
const fullName = ref("");
const password = ref("");
const captchaError = ref("");

const captchaWrapRef = ref<HTMLElement | null>(null);
const captchaOpen = ref(false);
const captchaScenePhase = ref<"idle" | "out" | "in">("idle");
const captchaFailAnimating = ref(false);
let captchaTransitionTimer: number | null = null;

const puzzleAreaRef = ref<HTMLElement | null>(null);
const pieceSize = 52;
const pieceStartX = 14;
const sliderX = ref(0);
const targetX = ref(0);
const targetY = ref(0);
const maxSlide = ref(180);
const sceneWidth = ref(320);
const sceneHeight = ref(160);
const puzzleVerified = ref(false);
const isDragging = ref(false);
const dragStartX = ref(0);
const dragStartSliderX = ref(0);
const captchaImage = ref("");

const IMAGE_POOL = [
  "https://picsum.photos/id/1043/900/450",
  "https://picsum.photos/id/1069/900/450",
  "https://picsum.photos/id/1074/900/450",
  "https://picsum.photos/id/1084/900/450",
];

const pieceX = computed(() => pieceStartX + sliderX.value);
const pieceVisible = ref(true);

const SHAPE_POOL = [
  "circle(50% at 50% 50%)",
  "polygon(50% 0%, 0% 100%, 100% 100%)",
  "polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)",
];
const shapeClipPath = ref(SHAPE_POOL[0]);
const lastShapeIndex = ref(0);
const lastImageIndex = ref(0);

function pickRandomShapeIndex(): number {
  if (SHAPE_POOL.length <= 1) return 0;
  let idx = Math.floor(Math.random() * SHAPE_POOL.length);
  if (idx === lastShapeIndex.value) {
    idx = (idx + 1 + Math.floor(Math.random() * (SHAPE_POOL.length - 1))) % SHAPE_POOL.length;
  }
  return idx;
}

function pickRandomImageIndex(): number {
  if (IMAGE_POOL.length <= 1) return 0;
  let idx = Math.floor(Math.random() * IMAGE_POOL.length);
  if (idx === lastImageIndex.value) {
    idx = (idx + 1 + Math.floor(Math.random() * (IMAGE_POOL.length - 1))) % IMAGE_POOL.length;
  }
  return idx;
}

function toggleCaptchaPopover() {
  captchaOpen.value = !captchaOpen.value;
  if (captchaOpen.value) {
    resetPuzzle();
  }
}

function closeCaptchaPopover() {
  captchaOpen.value = false;
}

function transitionToNewPuzzle(opts?: { message?: string; asFail?: boolean }) {
  if (captchaTransitionTimer) {
    window.clearTimeout(captchaTransitionTimer);
    captchaTransitionTimer = null;
  }

  if (opts?.message) captchaError.value = opts.message;
  captchaFailAnimating.value = !!opts?.asFail;
  captchaScenePhase.value = "out";

  // 等淡出结束后再真正换“图+形状”，避免瞬间跳变
  captchaTransitionTimer = window.setTimeout(() => {
    resetPuzzle({ keepError: true });
    captchaScenePhase.value = "in";
    captchaTransitionTimer = window.setTimeout(() => {
      captchaScenePhase.value = "idle";
      captchaFailAnimating.value = false;
      captchaTransitionTimer = null;
    }, 200);
  }, 220);
}

function onClickOutside(e: MouseEvent) {
  const el = captchaWrapRef.value;
  if (!el) return;
  const target = e.target as Node | null;
  if (target && !el.contains(target)) {
    closeCaptchaPopover();
  }
}

function resetPuzzle(opts?: { keepError?: boolean }) {
  const width = puzzleAreaRef.value?.clientWidth ?? 300;
  const height = puzzleAreaRef.value?.clientHeight ?? 160;
  sceneWidth.value = width;
  sceneHeight.value = height;
  maxSlide.value = Math.max(120, width - pieceSize - pieceStartX - 8);
  const min = 96;
  const max = Math.max(min + 24, width - pieceSize - 20);
  targetX.value = Math.round(min + Math.random() * (max - min));
  targetY.value = Math.round(16 + Math.random() * Math.max(16, height - pieceSize - 26));
  sliderX.value = 0;
  puzzleVerified.value = false;
  if (!opts?.keepError) captchaError.value = "";
  const imgIdx = pickRandomImageIndex();
  lastImageIndex.value = imgIdx;
  captchaImage.value = IMAGE_POOL[imgIdx];
  const shapeIdx = pickRandomShapeIndex();
  lastShapeIndex.value = shapeIdx;
  shapeClipPath.value = SHAPE_POOL[shapeIdx];
  pieceVisible.value = true;
}

function onSliderDown(e: PointerEvent) {
  if (puzzleVerified.value) return;
  isDragging.value = true;
  dragStartX.value = e.clientX;
  dragStartSliderX.value = sliderX.value;
  window.addEventListener("pointermove", onSliderMove);
  window.addEventListener("pointerup", onSliderUp);
}

function onSliderMove(e: PointerEvent) {
  if (!isDragging.value) return;
  const delta = e.clientX - dragStartX.value;
  const next = dragStartSliderX.value + delta;
  sliderX.value = Math.min(maxSlide.value, Math.max(0, next));
}

function onSliderUp() {
  if (!isDragging.value) return;
  isDragging.value = false;
  window.removeEventListener("pointermove", onSliderMove);
  window.removeEventListener("pointerup", onSliderUp);

  if (Math.abs(pieceX.value - targetX.value) <= 6) {
    sliderX.value = targetX.value - pieceStartX;
    puzzleVerified.value = true;
    captchaError.value = "";
    window.setTimeout(() => {
      pieceVisible.value = false;
      closeCaptchaPopover();
    }, 280);
    return;
  }

  captchaError.value = "验证失败，已为你刷新，请再试一次";
  transitionToNewPuzzle({ asFail: true });
}

function handleAuth() {
  if (!puzzleVerified.value) {
    captchaError.value = "请先完成滑动拼图验证码";
    captchaOpen.value = true;
    return;
  }
  // 这里先做原型占位：不跳转外链，只触发“已登录”事件或返回首页
  emit("authed");
}

onMounted(() => {
  resetPuzzle();
  window.addEventListener("resize", resetPuzzle);
  document.addEventListener("mousedown", onClickOutside);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resetPuzzle);
  window.removeEventListener("pointermove", onSliderMove);
  window.removeEventListener("pointerup", onSliderUp);
  document.removeEventListener("mousedown", onClickOutside);
  if (captchaTransitionTimer) window.clearTimeout(captchaTransitionTimer);
});

watch(mode, () => {
  resetPuzzle();
});
</script>

