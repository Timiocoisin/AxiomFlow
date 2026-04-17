<template>
  <div class="auth-shell min-h-screen flex flex-col">
    <!-- Navbar -->
    <nav class="sticky top-0 z-50 glass border-b border-white/10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16 items-center">
          <!-- Logo -->
          <button class="flex items-center gap-2" type="button" @click="emit('back')">
            <img alt="Axiomflow Logo" class="w-8 h-8 rounded-lg" src="/icons/favicon.svg" />
            <span class="text-xl font-bold tracking-tight text-slate-900 dark:text-white">Axiomflow</span>
          </button>
          <!-- Toolbar -->
          <div class="flex items-center gap-3">
            <!-- Theme toggle -->
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
              {{ t("common.back") }}
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
        <!-- Tabs -->
        <div class="flex p-1 rounded-xl mb-8 auth-tabs">
          <button
            class="flex-1 py-2 text-sm font-semibold rounded-lg shadow-sm transition-all"
            :class="mode === 'login' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'"
            type="button"
            @click="mode = 'login'"
          >
            {{ t("nav.login") }}
          </button>
          <button
            class="flex-1 py-2 text-sm font-semibold rounded-lg shadow-sm transition-all"
            :class="mode === 'register' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'"
            type="button"
            @click="mode = 'register'"
          >
            {{ t("auth.signup") }}
          </button>
        </div>

        <!-- Header -->
        <div class="mb-8">
          <h2 class="text-2xl font-bold mb-2">
            {{ mode === "login" ? t("auth.welcomeBack") : t("auth.createAccount") }}
          </h2>
          <p class="text-slate-400">
            {{
              mode === "login"
                ? t("auth.loginSubtitle")
                : t("auth.registerSubtitle")
            }}
          </p>
        </div>

        <!-- Form -->
        <form class="space-y-5" @submit.prevent="handleAuth">
          <div>
            <label class="block text-sm font-medium text-slate-400 mb-2">{{ t("auth.emailLabel") }}</label>
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
            <label class="block text-sm font-medium text-slate-400 mb-2">{{ t("auth.usernameLabel") }}</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                <Icon icon="ph:user-bold" />
              </span>
              <input
                v-model.trim="fullName"
                class="w-full auth-input rounded-xl py-3 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
                :placeholder="t('auth.usernamePlaceholder')"
                type="text"
              />
            </div>
          </div>

          <div>
            <div class="flex justify-between items-center mb-2">
              <label class="text-sm font-medium text-slate-400">{{ t("auth.passwordLabel") }}</label>
              <a
                v-if="mode === 'login'"
                class="text-xs text-indigo-400 hover:text-indigo-300"
                href="#"
                @click.prevent="openForgotModal"
                >{{ t("auth.forgotPassword") }}</a
              >
            </div>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                <Icon icon="ph:lock-key-bold" />
              </span>
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                class="w-full auth-input rounded-xl py-3 pl-12 pr-12 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
                placeholder="••••••••"
                required
              />
              <button
                class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
                type="button"
                @click="showPassword = !showPassword"
                aria-label="toggle password visibility"
              >
                <Icon :icon="showPassword ? 'ph:eye-slash-bold' : 'ph:eye-bold'" class="text-xl" />
              </button>
            </div>
            <p class="mt-2 text-xs text-slate-500 dark:text-slate-400">{{ t("auth.passwordRule") }}</p>
          </div>

          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <label class="text-sm font-medium text-slate-400">{{ t("auth.captchaLabel") }}</label>
              <span v-if="puzzleVerified" class="text-xs text-emerald-400">{{ t("auth.verified") }}</span>
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
                  {{ puzzleVerified ? t("auth.verifySuccess") : t("auth.clickToVerify") }}
                </span>
                <span class="text-xs text-slate-500 dark:text-slate-400">
                  {{ puzzleVerified ? t("auth.passed") : t("auth.needPuzzle") }}
                </span>
              </button>

              <div
                v-if="captchaOpen"
                class="captcha-popover absolute left-0 right-0 bottom-full mb-3 rounded-2xl border overflow-hidden min-w-[320px] max-w-[min(100vw-2rem,28rem)]"
              >
                <div class="captcha-popover-arrow"></div>
                <div class="p-4 space-y-3">
                  <div class="flex items-center justify-between">
                    <div class="text-sm font-semibold text-slate-100 dark:text-slate-100">{{ t("auth.sliderTitle") }}</div>
                    <button
                      class="text-xs text-indigo-300 hover:text-indigo-200 disabled:opacity-50"
                      type="button"
                      :disabled="captchaLoading"
                      @click="transitionToNewPuzzle()"
                    >
                      {{ t("auth.refresh") }}
                    </button>
                  </div>

                  <div
                    v-if="captchaLoading"
                    class="rounded-xl border bg-slate-900/60 border-slate-700/60 animate-pulse"
                    :style="{ width: `${sceneWidth}px`, height: `${sceneHeight}px`, maxWidth: '100%' }"
                  >
                    <div class="h-full w-full flex items-center justify-center text-xs text-slate-300">{{ t("auth.captchaLoading") }}</div>
                  </div>

                  <div
                    v-else
                    ref="puzzleAreaRef"
                    class="captcha-scene relative rounded-xl border overflow-hidden select-none"
                    :class="{
                      'captcha-scene--out': captchaScenePhase === 'out',
                      'captcha-scene--in': captchaScenePhase === 'in',
                      'captcha-scene--fail': captchaFailAnimating,
                    }"
                    :style="{
                      width: `${sceneWidth}px`,
                      height: `${sceneHeight}px`,
                      maxWidth: '100%',
                      backgroundImage: `url(${captchaImage})`,
                      backgroundSize: `${bgRenderWidth}px ${bgRenderHeight}px`,
                      backgroundPosition: `${bgOffsetX}px ${bgOffsetY}px`,
                      backgroundRepeat: 'no-repeat',
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
                        backgroundImage: `url(${captchaPieceImage})`,
                        backgroundSize: `${pieceSize}px ${pieceSize}px`,
                        backgroundPosition: 'center',
                        backgroundRepeat: 'no-repeat',
                        clipPath: shapeClipPath,
                        opacity: pieceVisible ? 1 : 0,
                      }"
                    >
                      <div class="piece-gloss"></div>
                    </div>

                    <div class="absolute bottom-2 left-3 text-[11px] text-slate-200/90">
                      {{ puzzleVerified ? t("auth.passed") : t("auth.sliderHint") }}
                    </div>
                  </div>

                  <div class="captcha-track relative h-12 rounded-xl border overflow-hidden">
                    <div class="captcha-track-fill absolute inset-y-0 left-0" :style="{ width: `${sliderX + 22}px` }"></div>
                    <div class="absolute inset-0 flex items-center justify-center text-xs font-medium text-slate-200/90 pointer-events-none">
                      {{ puzzleVerified ? t("auth.verifySuccess") : t("auth.sliderAction") }}
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

          <button
            class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3.5 rounded-xl transition-all shadow-lg shadow-indigo-600/20 active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed"
            type="submit"
            :disabled="authSubmitting"
          >
            {{ authSubmitting ? t("common.saving") : t("auth.continue") }}
          </button>

          <p v-if="authError" class="mt-3 text-xs text-rose-300">{{ authError }}</p>
        </form>

        <!-- Divider -->
        <div v-if="mode === 'login'" class="relative my-8">
          <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-slate-800"></div>
          </div>
          <div class="relative flex justify-center text-xs uppercase">
            <span class="auth-divider px-4 text-slate-500 tracking-widest">{{ t("auth.orContinueWith") }}</span>
          </div>
        </div>

        <!-- Social login -->
        <div v-if="mode === 'login'" class="grid grid-cols-2 gap-4">
          <button
            class="flex items-center justify-center gap-2 py-3 border border-slate-800 rounded-xl hover:bg-white/5 transition-all"
            type="button"
            @click="startOauth('google')"
          >
            <Icon class="text-lg" icon="logos:google-icon" />
            <span class="text-sm font-semibold">Google</span>
          </button>
          <button
            class="flex items-center justify-center gap-2 py-3 border border-slate-800 rounded-xl hover:bg-white/5 transition-all"
            type="button"
            @click="startOauth('github')"
          >
            <Icon class="text-lg text-slate-900 dark:text-white" icon="ri:github-fill" />
            <span class="text-sm font-semibold">GitHub</span>
          </button>
        </div>

        <p class="mt-8 text-center text-xs text-slate-500">
          {{ t("auth.tosLead") }}
          <a class="underline hover:text-slate-300" href="#" @click.prevent>{{ t("auth.terms") }}</a>
          {{ t("auth.and") }}
          <a class="underline hover:text-slate-300" href="#" @click.prevent>{{ t("auth.privacy") }}</a>
        </p>
      </div>

      <!-- Security hint -->
      <div class="mt-10 flex items-center gap-4 text-slate-500 text-sm">
        <span class="flex items-center gap-1.5"><Icon class="text-green-500" icon="ph:shield-check-bold" /> {{ t("auth.ssl") }}</span>
        <span class="w-1 h-1 rounded-full bg-slate-700"></span>
        <span class="flex items-center gap-1.5"><Icon class="text-indigo-400" icon="ph:fingerprint-bold" /> {{ t("auth.securityStandard") }}</span>
      </div>
    </div>
  </div>

  <div
    class="fixed inset-0 z-[60] flex items-center justify-center p-4 transition-all duration-300"
    :class="forgotOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'"
  >
    <div class="absolute inset-0 bg-slate-950/80 backdrop-blur-sm" @click="closeForgotModal"></div>
    <div class="relative w-full max-w-md auth-card rounded-3xl p-8 lg:p-10 shadow-2xl transition-all duration-300" :class="forgotOpen ? 'scale-100' : 'scale-95'">
      <button class="absolute right-6 top-6 text-slate-500 hover:text-slate-800 dark:hover:text-white transition-colors" type="button" @click="closeForgotModal">
        <Icon class="text-xl" icon="ph:x-bold" />
      </button>

      <div v-if="forgotStep === 1" class="space-y-6">
        <div class="mb-2">
          <h3 class="text-xl font-bold text-slate-900 dark:text-white mb-2">{{ t("auth.forgotTitle") }}</h3>
          <p class="text-slate-500 dark:text-slate-400 text-sm">{{ t("auth.forgotSubtitle") }}</p>
        </div>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-500 dark:text-slate-400 mb-2">{{ t("auth.emailLabel") }}</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                <Icon icon="ph:envelope-simple-bold" />
              </span>
              <input v-model.trim="forgotEmail" class="w-full rounded-xl py-3 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all border border-slate-200 bg-white/90 text-slate-900 placeholder:text-slate-400 dark:border-slate-800 dark:bg-slate-900/50 dark:text-white dark:placeholder:text-slate-500" placeholder="name@company.com" type="email" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-500 dark:text-slate-400 mb-2">{{ t("auth.mathCaptchaLabel") }}</label>
            <div class="flex gap-4">
              <div class="relative flex-grow">
                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                  <Icon icon="ph:shield-warning-bold" />
                </span>
                <input v-model.trim="forgotCaptchaInput" class="w-full rounded-xl py-3 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all border border-slate-200 bg-white/90 text-slate-900 placeholder:text-slate-400 dark:border-slate-800 dark:bg-slate-900/50 dark:text-white dark:placeholder:text-slate-500" :placeholder="t('auth.mathResultPlaceholder')" type="text" />
              </div>
              <button class="w-36 h-12 rounded-xl px-2 flex items-center justify-between font-mono text-[1.05rem] leading-none select-none transition-all border border-indigo-200/90 bg-white text-indigo-700 hover:border-indigo-400/90 hover:shadow-sm hover:shadow-indigo-500/12 dark:border-slate-700 dark:bg-slate-900 dark:text-indigo-300 dark:hover:border-indigo-500/50 overflow-hidden" type="button" @click="loadForgotMathCaptcha">
                <span class="flex-1 min-w-0 text-center whitespace-nowrap tracking-[0.06em]">{{ forgotMathCaptchaId ? forgotCaptchaText : t("auth.loading") }}</span>
                <span class="ml-1 shrink-0 w-7 h-7 rounded-lg inline-flex items-center justify-center border border-indigo-200/80 bg-indigo-50 text-indigo-600 dark:border-slate-600 dark:bg-slate-800 dark:text-indigo-300">
                  <Icon class="text-sm" icon="ph:arrows-clockwise-bold" />
                </span>
              </button>
            </div>
          </div>
          <button class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3.5 rounded-xl transition-all shadow-lg shadow-indigo-600/20 flex items-center justify-center gap-2" type="button" @click="toForgotStep2">
            <span>{{ t("auth.getCode") }}</span>
            <Icon icon="ph:arrow-right-bold" />
          </button>
          <p v-if="forgotError" class="text-xs text-rose-400">{{ forgotError }}</p>
        </div>
      </div>

      <div v-else-if="forgotStep === 2" class="space-y-6">
        <div class="mb-2">
          <h3 class="text-xl font-bold text-slate-900 dark:text-white mb-2">{{ t("auth.resetCodeTitle") }}</h3>
          <p class="text-slate-500 dark:text-slate-400 text-sm">
            {{ t("auth.resetCodeSentPrefix") }} <span>{{ forgotEmail || t("auth.yourEmail") }}</span>{{ t("auth.resetCodeSentSuffix") }}
          </p>
        </div>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-500 dark:text-slate-400 mb-2">{{ t("auth.resetCodeLabel") }}</label>
            <input
              v-model.trim="forgotResetToken"
              class="w-full h-12 px-4 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/50 font-medium transition-all border border-slate-200 bg-white/90 text-slate-900 dark:border-slate-800 dark:bg-slate-900/50 dark:text-white"
              :placeholder="t('auth.resetCodePlaceholder')"
              type="text"
            />
          </div>
          <button class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3.5 rounded-xl transition-all shadow-lg shadow-indigo-600/20 flex items-center justify-center gap-2" type="button" @click="toForgotStep3">
            <span>{{ t("auth.verifyAndContinue") }}</span>
          </button>
          <div class="text-center space-y-1">
            <button class="text-xs text-slate-500 hover:text-indigo-400 transition-colors disabled:opacity-50" :disabled="forgotResendLeft > 0" type="button" @click="restartForgotResend">
              {{ forgotResendLeft > 0 ? t("auth.resendCodeCountdown", { s: forgotResendLeft }) : t("auth.resendCode") }}
            </button>
            <p class="text-[11px] text-slate-400">{{ t("auth.resendHint") }}</p>
          </div>
          <p v-if="forgotError" class="text-xs text-rose-400">{{ forgotError }}</p>
        </div>
      </div>

      <div v-else class="space-y-6">
        <div class="mb-2">
          <h3 class="text-xl font-bold text-slate-900 dark:text-white mb-2">{{ t("auth.setNewPasswordTitle") }}</h3>
          <p class="text-slate-500 dark:text-slate-400 text-sm">{{ t("auth.setNewPasswordSubtitle") }}</p>
        </div>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-500 dark:text-slate-400 mb-2">{{ t("auth.newPasswordLabel") }}</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500"><Icon icon="ph:lock-key-bold" /></span>
              <input
                v-model="forgotNewPassword"
                class="w-full rounded-xl py-3 pl-12 pr-12 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all border border-slate-200 bg-white/90 text-slate-900 placeholder:text-slate-400 dark:border-slate-800 dark:bg-slate-900/50 dark:text-white dark:placeholder:text-slate-500"
                placeholder="••••••••"
                :type="showForgotNewPassword ? 'text' : 'password'"
              />
              <button
                class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
                type="button"
                @click="showForgotNewPassword = !showForgotNewPassword"
                aria-label="toggle password visibility"
              >
                <Icon :icon="showForgotNewPassword ? 'ph:eye-slash-bold' : 'ph:eye-bold'" class="text-xl" />
              </button>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-500 dark:text-slate-400 mb-2">{{ t("auth.confirmNewPasswordLabel") }}</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500"><Icon icon="ph:lock-key-bold" /></span>
              <input
                v-model="forgotConfirmPassword"
                class="w-full rounded-xl py-3 pl-12 pr-12 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all border border-slate-200 bg-white/90 text-slate-900 placeholder:text-slate-400 dark:border-slate-800 dark:bg-slate-900/50 dark:text-white dark:placeholder:text-slate-500"
                placeholder="••••••••"
                :type="showForgotConfirmPassword ? 'text' : 'password'"
              />
              <button
                class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
                type="button"
                @click="showForgotConfirmPassword = !showForgotConfirmPassword"
                aria-label="toggle password visibility"
              >
                <Icon :icon="showForgotConfirmPassword ? 'ph:eye-slash-bold' : 'ph:eye-bold'" class="text-xl" />
              </button>
            </div>
          </div>
          <button class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3.5 rounded-xl transition-all shadow-lg shadow-indigo-600/20 flex items-center justify-center gap-2" type="button" @click="finishReset">
            <span>{{ t("auth.finishReset") }}</span>
          </button>
          <p v-if="forgotError" class="text-xs text-rose-400">{{ forgotError }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { Icon } from "@iconify/vue";
import * as authApi from "./api/auth";

const emit = defineEmits<{
  (e: "back"): void;
  (e: "authed", payload: { accessToken: string; accessExpiresAt?: string }): void;
  (e: "verify-email", payload: { email: string }): void;
  (e: "toggle-theme"): void;
}>();

defineProps<{
  isDark: boolean;
}>();

const { locale, t } = useI18n();

const mode = ref<"login" | "register">("login");
const email = ref("");
const fullName = ref("");
const password = ref("");
const showPassword = ref(false);
const authSubmitting = ref(false);
const captchaError = ref("");
const authError = ref("");
const forgotOpen = ref(false);
const forgotStep = ref<1 | 2 | 3>(1);
const forgotEmail = ref("");
const forgotCaptchaInput = ref("");
const forgotMathLeft = ref(0);
const forgotMathRight = ref(0);
const forgotMathCaptchaId = ref("");
const forgotOtpDigits = ref(["", "", "", "", "", ""]);
const forgotResetToken = ref("");
const forgotResendLeft = ref(59);
const forgotNewPassword = ref("");
const forgotConfirmPassword = ref("");
const showForgotNewPassword = ref(false);
const showForgotConfirmPassword = ref(false);
const forgotError = ref("");
let forgotTimer: number | null = null;

const serverCaptchaId = ref("");
const committedPieceFinalX = ref(0);

const captchaWrapRef = ref<HTMLElement | null>(null);
const captchaOpen = ref(false);
const captchaLoading = ref(false);
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
const bgRenderWidth = ref(320);
const bgRenderHeight = ref(160);
const bgOffsetX = ref(0);
const bgOffsetY = ref(0);
const puzzleVerified = ref(false);
const isDragging = ref(false);
const dragStartX = ref(0);
const dragStartSliderX = ref(0);
const captchaImage = ref("");
const captchaPieceImage = ref("");
const imageNaturalWidth = ref(900);
const imageNaturalHeight = ref(450);

const pieceX = computed(() => pieceStartX + sliderX.value);
const pieceVisible = ref(true);

const SHAPE_POOL = ["circle(50% at 50% 50%)"];
const shapeClipPath = ref(SHAPE_POOL[0]);

async function loadImageNaturalSize(url: string): Promise<{ width: number; height: number } | null> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      if (img.naturalWidth > 0 && img.naturalHeight > 0) {
        resolve({ width: img.naturalWidth, height: img.naturalHeight });
      } else {
        resolve(null);
      }
    };
    img.onerror = () => resolve(null);
    img.src = url;
  });
}

function applyContainMetrics() {
  const iw = imageNaturalWidth.value;
  const ih = imageNaturalHeight.value;
  const sw = sceneWidth.value;
  const sh = sceneHeight.value;
  if (iw <= 0 || ih <= 0 || sw <= 0 || sh <= 0) return;

  // Fill captcha area using cover mode
  const scale = Math.max(sw / iw, sh / ih);
  bgRenderWidth.value = iw * scale;
  bgRenderHeight.value = ih * scale;
  bgOffsetX.value = (sw - bgRenderWidth.value) / 2;
  bgOffsetY.value = (sh - bgRenderHeight.value) / 2;
}

async function syncBackgroundMetrics() {
  if (!captchaImage.value) return;
  const size = await loadImageNaturalSize(captchaImage.value);
  if (size) {
    imageNaturalWidth.value = size.width;
    imageNaturalHeight.value = size.height;
  }
  applyContainMetrics();
}

function detectHoleTopLeftFromPngDataUrl(dataUrl: string, sw: number, sh: number): Promise<{ x: number; y: number } | null> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      try {
        const c = document.createElement("canvas");
        c.width = sw;
        c.height = sh;
        const ctx = c.getContext("2d");
        if (!ctx) {
          resolve(null);
          return;
        }
        ctx.drawImage(img, 0, 0, sw, sh);
        const data = ctx.getImageData(0, 0, sw, sh).data;
        let minX = sw;
        let minY = sh;
        let maxX = 0;
        let maxY = 0;
        let found = false;
        const alphaThresh = 48;
        for (let y = 0; y < sh; y++) {
          for (let x = 0; x < sw; x++) {
            const a = data[(y * sw + x) * 4 + 3];
            if (a < alphaThresh) {
              found = true;
              minX = Math.min(minX, x);
              minY = Math.min(minY, y);
              maxX = Math.max(maxX, x);
              maxY = Math.max(maxY, y);
            }
          }
        }
        if (!found || maxX < minX) {
          resolve(null);
          return;
        }
        resolve({ x: minX, y: minY });
      } catch {
        resolve(null);
      }
    };
    img.onerror = () => resolve(null);
    img.src = dataUrl;
  });
}

async function loadSlideChallengeAndReset(opts?: { keepError?: boolean }) {
  captchaLoading.value = true;
  await nextTick();
  const sceneRect = puzzleAreaRef.value?.getBoundingClientRect();
  const reqW = Math.round(sceneRect?.width || puzzleAreaRef.value?.clientWidth || sceneWidth.value || 320);
  const reqH = Math.round(sceneRect?.height || puzzleAreaRef.value?.clientHeight || sceneHeight.value || 160);

  let ch: Awaited<ReturnType<typeof authApi.issueSlideCaptcha>>;
  try {
    ch = await authApi.issueSlideCaptcha(reqW, reqH);
  } catch {
    captchaError.value = t("auth.errCaptchaLoad");
    captchaLoading.value = false;
    return;
  }

  const w = ch.scene_width;
  const h = ch.scene_height;
  sceneWidth.value = w;
  sceneHeight.value = h;
  captchaImage.value = `data:image/png;base64,${ch.image_base64}`;
  captchaPieceImage.value = `data:image/png;base64,${ch.piece_image_base64}`;

  await syncBackgroundMetrics();
  applyContainMetrics();
  maxSlide.value = Math.max(120, w - pieceSize - pieceStartX - 8);

  const hole = await detectHoleTopLeftFromPngDataUrl(captchaImage.value, w, h);
  if (!hole) {
    captchaError.value = t("auth.errCaptchaParse");
    captchaLoading.value = false;
    return;
  }

  serverCaptchaId.value = ch.captcha_id;
  // Server PNG uses a circular cutout; mask and piece must stay circular
  shapeClipPath.value = SHAPE_POOL[0];
  targetX.value = hole.x;
  targetY.value = hole.y;
  sliderX.value = 0;
  puzzleVerified.value = false;
  committedPieceFinalX.value = 0;
  if (!opts?.keepError) captchaError.value = "";

  pieceVisible.value = true;
  captchaLoading.value = false;
}

function invalidateClientCaptcha() {
  puzzleVerified.value = false;
  committedPieceFinalX.value = 0;
  serverCaptchaId.value = "";
  captchaImage.value = "";
  captchaPieceImage.value = "";
  captchaLoading.value = false;
}

async function toggleCaptchaPopover() {
  if (captchaOpen.value) {
    captchaOpen.value = false;
    return;
  }
  captchaOpen.value = true;
  // Prefer preloaded challenge/image to avoid waiting on click.
  if (!serverCaptchaId.value || !captchaImage.value) {
    await nextTick();
    await loadSlideChallengeAndReset();
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

  // Wait for fade-out before swapping scene to avoid sudden jumps
  captchaTransitionTimer = window.setTimeout(() => {
    void loadSlideChallengeAndReset({ keepError: true }).then(() => {
      captchaScenePhase.value = "in";
      captchaTransitionTimer = window.setTimeout(() => {
        captchaScenePhase.value = "idle";
        captchaFailAnimating.value = false;
        captchaTransitionTimer = null;
      }, 200);
    });
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

const forgotCaptchaText = computed(() => `${forgotMathLeft.value} + ${forgotMathRight.value} = ?`);

async function loadForgotMathCaptcha() {
  forgotError.value = "";
  try {
    const m = await authApi.issueMathCaptcha();
    forgotMathCaptchaId.value = m.captcha_id;
    forgotMathLeft.value = m.left;
    forgotMathRight.value = m.right;
    forgotCaptchaInput.value = "";
  } catch {
    forgotError.value = t("auth.errMathLoad");
  }
}

function resetForgotFlow() {
  forgotStep.value = 1;
  forgotEmail.value = "";
  forgotCaptchaInput.value = "";
  forgotOtpDigits.value = ["", "", "", "", "", ""];
  forgotResetToken.value = "";
  forgotResendLeft.value = 59;
  forgotNewPassword.value = "";
  forgotConfirmPassword.value = "";
  forgotError.value = "";
  if (forgotTimer) {
    window.clearInterval(forgotTimer);
    forgotTimer = null;
  }
  void loadForgotMathCaptcha();
}

function openForgotModal() {
  forgotOpen.value = true;
  resetForgotFlow();
}

function closeForgotModal() {
  forgotOpen.value = false;
}

function restartForgotResend() {
  forgotResendLeft.value = 59;
  forgotStep.value = 1;
  forgotCaptchaInput.value = "";
  forgotError.value = "";
  void loadForgotMathCaptcha();
}

function runForgotResendTimer() {
  if (forgotTimer) window.clearInterval(forgotTimer);
  forgotTimer = window.setInterval(() => {
    if (forgotResendLeft.value <= 0) {
      if (forgotTimer) window.clearInterval(forgotTimer);
      forgotTimer = null;
      return;
    }
    forgotResendLeft.value -= 1;
  }, 1000);
}

function toForgotStep2() {
  forgotError.value = "";
  if (!forgotEmail.value || !forgotEmail.value.includes("@")) {
    forgotError.value = t("auth.errEmailInvalid");
    return;
  }
  const answer = Number(forgotCaptchaInput.value);
  if (!Number.isFinite(answer)) {
    forgotError.value = t("auth.errMathResult");
    return;
  }
  if (!forgotMathCaptchaId.value) {
    forgotError.value = t("auth.errCaptchaExpired");
    void loadForgotMathCaptcha();
    return;
  }
  authApi
    .requestPasswordReset({
      email: forgotEmail.value,
      captcha_id: forgotMathCaptchaId.value,
      captcha_answer: Math.trunc(answer),
    })
    .then(() => {
      forgotStep.value = 2;
      forgotResendLeft.value = 59;
      runForgotResendTimer();
    })
    .catch((err) => {
      const detail = err?.response?.data?.detail;
      if (detail === "invalid_math_captcha") {
        forgotError.value = t("auth.errMathInvalid");
        void loadForgotMathCaptcha();
        return;
      }
      forgotError.value = t("auth.errSendFailed");
    });
}

function toForgotStep3() {
  forgotError.value = "";
  const code = forgotResetToken.value.trim();
  if (!/^[A-Za-z0-9]{6}$/.test(code)) {
    forgotError.value = t("auth.errResetCodeInvalid");
    return;
  }
  forgotStep.value = 3;
}

function finishReset() {
  forgotError.value = "";
  if (!forgotNewPassword.value || forgotNewPassword.value.length < 8) {
    forgotError.value = t("auth.errPasswordRule1");
    return;
  }
  if (!/[A-Za-z]/.test(forgotNewPassword.value) || !/\d/.test(forgotNewPassword.value)) {
    forgotError.value = t("auth.errPasswordRule2");
    return;
  }
  if (forgotNewPassword.value !== forgotConfirmPassword.value) {
    forgotError.value = t("auth.errPasswordMismatch");
    return;
  }
  authApi
    .resetPassword({ token: forgotResetToken.value, new_password: forgotNewPassword.value })
    .then(() => {
      closeForgotModal();
    })
    .catch(() => {
      forgotError.value = t("auth.errResetFailed");
    });
}

function resetPuzzle(opts?: { keepError?: boolean }) {
  const sceneRect = puzzleAreaRef.value?.getBoundingClientRect();
  const width = Math.round(sceneRect?.width || puzzleAreaRef.value?.clientWidth || sceneWidth.value || 300);
  const height = Math.round(sceneRect?.height || puzzleAreaRef.value?.clientHeight || sceneHeight.value || 160);
  sceneWidth.value = width;
  sceneHeight.value = height;
  applyContainMetrics();
  maxSlide.value = Math.max(120, width - pieceSize - pieceStartX - 8);
  sliderX.value = 0;
  puzzleVerified.value = false;
  if (!opts?.keepError) captchaError.value = "";
  shapeClipPath.value = SHAPE_POOL[0];
  pieceVisible.value = true;
}

function onSliderDown(e: PointerEvent) {
  if (puzzleVerified.value) return;
  e.preventDefault();
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

  if (Math.abs(pieceX.value - targetX.value) <= 14) {
    sliderX.value = targetX.value - pieceStartX;
    committedPieceFinalX.value = targetX.value;
    puzzleVerified.value = true;
    captchaError.value = "";
    window.setTimeout(() => {
      pieceVisible.value = false;
      closeCaptchaPopover();
    }, 280);
    return;
  }

  captchaError.value = t("auth.errVerifyFailed");
  transitionToNewPuzzle({ asFail: true });
}

function startOauth(provider: "google" | "github") {
  window.location.href = authApi.oauthStartUrl(provider);
}

function handleAuth() {
  if (authSubmitting.value) return;
  authError.value = "";
  if (!puzzleVerified.value) {
    captchaError.value = t("auth.errNeedCaptcha");
    captchaOpen.value = true;
    return;
  }
  authSubmitting.value = true;
  if (mode.value === "register") {
    const username = fullName.value.trim();
    if (!username) {
      captchaError.value = t("auth.errNeedUsername");
      authSubmitting.value = false;
      return;
    }
    authApi
      .register({
        email: email.value,
        username,
        password: password.value,
        captcha_id: serverCaptchaId.value,
        piece_final_x: committedPieceFinalX.value,
      })
      .then((res) => {
        if (res?.message === "verification_email_send_failed") {
          authError.value = t("auth.errVerifyMailFailed");
          return;
        }
        localStorage.setItem("axiomflow:lastRegisterEmail", email.value);
        emit("verify-email", { email: email.value });
      })
      .catch((err) => {
        invalidateClientCaptcha();
        const detail = err?.response?.data?.detail;
        if (err?.response?.status === 422) {
          authError.value = t("auth.errRegisterValidation");
          return;
        }
        if (err?.response?.status === 400 && detail === "invalid_slide_captcha") {
          authError.value = t("auth.errSlideExpired");
          return;
        }
        if (err?.response?.status === 409 && detail === "username_taken") {
          authError.value = t("auth.errUsernameTaken");
          return;
        }
        if (err?.response?.status === 409) {
          authError.value = t("auth.errEmailTaken");
          return;
        }
        authError.value = t("auth.errRegisterFailed");
      })
      .finally(() => {
        authSubmitting.value = false;
      });
    return;
  }

  authApi
    .login({
      email: email.value,
      password: password.value,
      captcha_id: serverCaptchaId.value,
      piece_final_x: committedPieceFinalX.value,
    })
    .then((res) => {
      emit("authed", { accessToken: res.access_token, accessExpiresAt: res.access_expires_at });
    })
    .catch((err) => {
      invalidateClientCaptcha();
      const detail = err?.response?.data?.detail;
      if (err?.response?.status === 403 && detail === "email_not_verified") {
        authError.value = t("auth.errNeedEmailVerify");
        emit("verify-email", { email: email.value });
        return;
      }
      if (err?.response?.status === 400 && detail === "invalid_slide_captcha") {
        authError.value = t("auth.errSlideExpired");
        return;
      }
      if (err?.response?.status === 401) {
        authError.value = t("auth.errInvalidCredentials");
        return;
      }
      authError.value = t("auth.errLoginFailed");
    })
    .finally(() => {
      authSubmitting.value = false;
    });
}

onMounted(() => {
  resetPuzzle();
  // Preload slide captcha as soon as auth page is mounted.
  void loadSlideChallengeAndReset({ keepError: true });

  window.addEventListener("resize", () => {
    if (captchaOpen.value) {
      void loadSlideChallengeAndReset();
    } else {
      resetPuzzle();
    }
  });
  document.addEventListener("mousedown", onClickOutside);
});

onBeforeUnmount(() => {
  // resize listener uses anonymous callback; browser cleanup on unmount is enough
  window.removeEventListener("pointermove", onSliderMove);
  window.removeEventListener("pointerup", onSliderUp);
  document.removeEventListener("mousedown", onClickOutside);
  if (captchaTransitionTimer) window.clearTimeout(captchaTransitionTimer);
  if (forgotTimer) window.clearInterval(forgotTimer);
});

watch(mode, () => {
  invalidateClientCaptcha();
  resetPuzzle();
  // Preload a fresh challenge when switching login/register tab.
  void loadSlideChallengeAndReset({ keepError: true });
});
</script>

