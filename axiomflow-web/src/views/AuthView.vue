<template>
  <div class="auth-container">
    <div class="auth-card glass-card">
      <div class="auth-header">
        <div class="auth-logo">
          <img src="/icons/favicon.svg" alt="AxiomFlow" class="auth-logo-image" />
          <div class="auth-logo-text">AxiomFlow</div>
        </div>
        <h1 class="auth-title">{{ isLogin ? "欢迎回来" : "创建账户" }}</h1>
        <p class="auth-subtitle">{{ isLogin ? "登录以继续使用" : "注册新账户开始使用" }}</p>
      </div>

      <div class="auth-form">
        <form @submit.prevent="handleSubmit">
          <div v-if="!isLogin" class="form-group">
            <label class="form-label">用户名</label>
            <div class="input-wrapper">
              <input
                v-model="formData.name"
                type="text"
                class="form-input"
                :class="{ 'input-error': nameError, 'input-valid': nameValid }"
                placeholder="请输入用户名"
                autocomplete="username"
                aria-required="true"
                aria-invalid="!!nameError"
                aria-describedby="name-error"
                @blur="validateName"
                @input="validateName"
                @keyup.enter="handleSubmit"
                required
              />
              <div v-if="nameValid && formData.name" class="input-status-icon input-status-success">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div v-if="nameError" class="input-status-icon input-status-error">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
            </div>
            <div v-if="nameError" id="name-error" class="field-error" role="alert">{{ nameError }}</div>
          </div>

          <div class="form-group">
            <label class="form-label">邮箱</label>
            <div class="input-wrapper">
              <input
                v-model="formData.email"
                type="email"
                class="form-input"
                :class="{ 'input-error': emailError, 'input-valid': emailValid }"
                placeholder="请输入邮箱地址"
                autocomplete="email"
                aria-required="true"
                aria-invalid="!!emailError"
                aria-describedby="email-error"
                @blur="validateEmail"
                @input="validateEmail"
                @keyup.enter="handleSubmit"
                required
              />
              <div v-if="emailValid && formData.email" class="input-status-icon input-status-success">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div v-if="emailError" class="input-status-icon input-status-error">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
            </div>
            <div v-if="emailError" id="email-error" class="field-error" role="alert">{{ emailError }}</div>
          </div>

          <div class="form-group">
            <label class="form-label">密码</label>
            <div class="password-input-wrapper">
              <input
                v-model="formData.password"
                :type="showPassword ? 'text' : 'password'"
                class="form-input"
                :class="{ 'input-error': passwordError, 'input-valid': passwordValid && formData.password }"
                placeholder="请输入密码"
                autocomplete="current-password"
                aria-required="true"
                aria-invalid="!!passwordError"
                aria-describedby="password-error"
                @blur="validatePassword"
                @input="validatePassword"
                @keyup.enter="handleSubmit"
                required
                :minlength="isLogin ? 0 : 8"
              />
              <button
                type="button"
                class="password-toggle"
                @click="showPassword = !showPassword"
                tabindex="-1"
              >
                <svg v-if="showPassword" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 12S5 4 12 4S23 12 23 12S19 20 12 20S1 12 1 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20C7 20 2.73 16.39 1 12C2.73 7.61 7 4 12 4C13.5 4 14.9 4.35 16.12 4.95L17.94 3.13M17.94 17.94L3.13 3.13M17.94 17.94L20.87 20.87M3.13 3.13L1 1M20.87 20.87L23 23" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
            <div v-if="passwordError" id="password-error" class="field-error" role="alert">{{ passwordError }}</div>
            <!-- 密码强度指示器 -->
            <div v-if="!isLogin && formData.password" class="password-strength">
              <div class="strength-bar" :class="passwordStrengthClass"></div>
              <span class="strength-text">{{ passwordStrengthText }}</span>
            </div>
          </div>

          <div v-if="!isLogin" class="form-group">
            <label class="form-label">确认密码</label>
            <div class="password-input-wrapper">
              <input
                v-model="formData.confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                class="form-input"
                :class="{ 'input-error': confirmPasswordError, 'input-valid': confirmPasswordValid && formData.confirmPassword }"
                placeholder="请再次输入密码"
                autocomplete="new-password"
                aria-required="true"
                aria-invalid="!!confirmPasswordError"
                aria-describedby="confirm-password-error"
                @blur="validateConfirmPassword"
                @input="validateConfirmPassword"
                @keyup.enter="handleSubmit"
                required
              />
              <button
                type="button"
                class="password-toggle"
                @click="showConfirmPassword = !showConfirmPassword"
                tabindex="-1"
              >
                <svg v-if="showConfirmPassword" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 12S5 4 12 4S23 12 23 12S19 20 12 20S1 12 1 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20C7 20 2.73 16.39 1 12C2.73 7.61 7 4 12 4C13.5 4 14.9 4.35 16.12 4.95L17.94 3.13M17.94 17.94L3.13 3.13M17.94 17.94L20.87 20.87M3.13 3.13L1 1M20.87 20.87L23 23" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
            <div v-if="confirmPasswordError" id="confirm-password-error" class="field-error" role="alert">{{ confirmPasswordError }}</div>
          </div>

          <div v-if="error" class="error-message">
            {{ error }}
          </div>

          <!-- 验证码（注册和登录时显示） -->
          <div class="form-group">
            <label class="form-label">验证码</label>
            <div class="captcha-wrapper">
              <div class="input-wrapper" style="flex: 1;">
                <input
                  v-model="captchaCode"
                  type="text"
                  class="form-input"
                  :class="{ 'input-error': captchaError, 'input-valid': captchaCode && !captchaError }"
                  placeholder="请输入验证码"
                  maxlength="4"
                  autocomplete="off"
                  aria-label="验证码输入"
                  @keyup.enter="handleSubmit"
                />
                <div v-if="captchaCode && !captchaError" class="input-status-icon input-status-success">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
                <div v-if="captchaError" class="input-status-icon input-status-error">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
              </div>
              <div class="captcha-image-wrapper">
                <img
                  v-if="captchaImage"
                  :src="captchaImage"
                  alt="验证码"
                  class="captcha-image"
                  @click="loadCaptcha"
                  role="button"
                  tabindex="0"
                  aria-label="点击刷新验证码"
                  @keyup.enter="loadCaptcha"
                />
                <div v-else class="captcha-placeholder" @click="loadCaptcha" role="button" tabindex="0" aria-label="点击加载验证码">
                  <svg v-if="loadingCaptcha" class="captcha-loading" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-dasharray="31.416" stroke-dashoffset="31.416">
                      <animate attributeName="stroke-dasharray" dur="2s" values="0 31.416;15.708 15.708;0 31.416;0 31.416" repeatCount="indefinite"/>
                      <animate attributeName="stroke-dashoffset" dur="2s" values="0;-15.708;-31.416;-31.416" repeatCount="indefinite"/>
                    </circle>
                  </svg>
                  <span v-else>点击加载</span>
                </div>
                <button
                  type="button"
                  class="captcha-refresh"
                  @click="loadCaptcha"
                  :disabled="loadingCaptcha"
                  aria-label="刷新验证码"
                  title="刷新验证码"
                >
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M3 12C3 7.03 7.03 3 12 3C16.97 3 21 7.03 21 12M21 12L17 8M21 12L17 16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
              </div>
            </div>
            <div v-if="captchaError" class="field-error">{{ captchaError }}</div>
          </div>

          <!-- 记住我选项（仅登录时显示） -->
          <div v-if="isLogin" class="form-options">
            <label class="checkbox-label">
              <input 
                type="checkbox" 
                v-model="rememberMe"
                class="checkbox-input"
                aria-label="记住我"
              />
              <span class="checkbox-custom"></span>
              <span class="checkbox-text">记住我</span>
            </label>
            <button
              type="button"
              class="forgot-password-link"
              @click="showForgotPasswordModal = true"
              :disabled="loading"
              aria-label="忘记密码"
            >
              忘记密码？
            </button>
          </div>

          <button 
            type="submit" 
            class="auth-button" 
            :disabled="loading || !isFormValid"
            :aria-busy="loading"
            aria-label="提交表单"
          >
            <span v-if="loading" class="loading-spinner" aria-hidden="true"></span>
            <span>{{ loading ? (isLogin ? "登录中..." : "注册中...") : (isLogin ? "登录" : "注册") }}</span>
          </button>
        </form>

        <div class="auth-divider">
          <span>或</span>
        </div>

        <div class="social-login">
          <button 
            class="social-button social-github" 
            @click="handleSocialLogin('github')"
            :disabled="loading"
          >
            <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.01-1.023-.014-1.856-2.782.604-3.369-1.18-3.369-1.18-.455-1.157-1.11-1.466-1.11-1.466-.907-.62.068-.607.068-.607 1.003.07 1.53 1.03 1.53 1.03.892 1.53 2.341 1.088 2.91.832.09-.647.35-1.088.636-1.338-2.22-.252-4.555-1.11-4.555-4.943 0-1.092.39-1.986 1.03-2.685-.103-.253-.446-1.27.098-2.646 0 0 .84-.269 2.75 1.026A9.56 9.56 0 0 1 12 6.844c.85.004 1.705.115 2.505.336 1.909-1.295 2.748-1.026 2.748-1.026.546 1.376.202 2.393.1 2.646.64.699 1.028 1.593 1.028 2.685 0 3.842-2.339 4.688-4.566 4.935.359.309.678.92.678 1.855 0 1.338-.012 2.416-.012 2.744 0 .267.18.578.688.48A10.02 10.02 0 0 0 22 12c0-5.523-4.477-10-10-10z"/>
            </svg>
            <span>GitHub登录</span>
          </button>
          <button 
            class="social-button social-google" 
            @click="handleSocialLogin('google')"
            :disabled="loading"
          >
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            <span>Google登录</span>
          </button>
        </div>

        <div class="auth-footer">
          <span>{{ isLogin ? "还没有账户？" : "已有账户？" }}</span>
          <button class="auth-link" @click="toggleMode" :disabled="loading" aria-label="切换登录/注册模式">
            {{ isLogin ? "立即注册" : "立即登录" }}
          </button>
        </div>
      </div>
    </div>

    <!-- 忘记密码模态框 -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showForgotPasswordModal"
          class="modal-overlay"
          @click.self="showForgotPasswordModal = false"
          role="dialog"
          aria-labelledby="forgot-password-title"
          aria-modal="true"
        >
          <div class="modal-content glass-card">
            <div class="modal-header">
              <h2 id="forgot-password-title">忘记密码</h2>
              <button
                class="modal-close"
                @click="showForgotPasswordModal = false"
                aria-label="关闭"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
            <div class="modal-body">
              <div v-if="!forgotPasswordSuccess">
                <p class="modal-description">请输入您的邮箱地址，我们将发送密码重置链接到您的邮箱。</p>
                <div class="form-group">
                  <label class="form-label" for="forgot-email">邮箱地址</label>
                  <div class="input-wrapper">
                    <input
                      id="forgot-email"
                      v-model="forgotPasswordEmail"
                      type="email"
                      class="form-input"
                      placeholder="请输入邮箱地址"
                      autocomplete="email"
                      aria-required="true"
                      @keyup.enter="handleForgotPassword"
                    />
                  </div>
                </div>
                <button
                  class="auth-button"
                  @click="handleForgotPassword"
                  :disabled="forgotPasswordLoading"
                  style="width: 100%; margin-top: 20px;"
                >
                  <span v-if="forgotPasswordLoading" class="loading-spinner"></span>
                  <span>{{ forgotPasswordLoading ? "发送中..." : "发送重置链接" }}</span>
                </button>
              </div>
              <div v-else class="forgot-password-success">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="success-icon">
                  <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                </svg>
                <p>重置链接已发送到您的邮箱，请查收。</p>
                <p class="success-hint">（开发环境：请查看控制台或Toast提示中的重置链接）</p>
                <button
                  class="auth-button"
                  @click="showForgotPasswordModal = false"
                  style="width: 100%; margin-top: 20px;"
                >
                  确定
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 重置密码模态框 -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showResetPasswordModal"
          class="modal-overlay"
          @click.self="showResetPasswordModal = false"
          role="dialog"
          aria-labelledby="reset-password-title"
          aria-modal="true"
        >
          <div class="modal-content glass-card">
            <div class="modal-header">
              <h2 id="reset-password-title">重置密码</h2>
              <button
                class="modal-close"
                @click="showResetPasswordModal = false"
                aria-label="关闭"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
            <div class="modal-body">
              <div class="form-group">
                <label class="form-label" for="reset-password">新密码</label>
                <div class="password-input-wrapper">
                  <input
                    id="reset-password"
                    v-model="resetPasswordData.password"
                    type="password"
                    class="form-input"
                    placeholder="请输入新密码（至少8位）"
                    autocomplete="new-password"
                    aria-required="true"
                    minlength="8"
                    @keyup.enter="handleResetPassword"
                  />
                </div>
              </div>
              <div class="form-group">
                <label class="form-label" for="reset-confirm-password">确认密码</label>
                <div class="password-input-wrapper">
                  <input
                    id="reset-confirm-password"
                    v-model="resetPasswordData.confirmPassword"
                    type="password"
                    class="form-input"
                    placeholder="请再次输入新密码"
                    autocomplete="new-password"
                    aria-required="true"
                    @keyup.enter="handleResetPassword"
                  />
                </div>
              </div>
              <button
                class="auth-button"
                @click="handleResetPassword"
                :disabled="resetPasswordLoading || !resetPasswordData.password || !resetPasswordData.confirmPassword"
                style="width: 100%; margin-top: 20px;"
              >
                <span v-if="resetPasswordLoading" class="loading-spinner"></span>
                <span>{{ resetPasswordLoading ? "重置中..." : "重置密码" }}</span>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";
import { API_BASE, googleLogin, emailRegister, emailLogin, getCaptcha, forgotPassword, resetPassword } from "@/lib/api";

const router = useRouter();
const userStore = useUserStore();

const isLogin = ref(true);
const loading = ref(false);
const error = ref("");
const showPassword = ref(false);
const showConfirmPassword = ref(false);
const rememberMe = ref(true); // 默认记住我

// 验证码相关
const captchaImage = ref<string | null>(null);
const captchaSession = ref<string>("");
const captchaCode = ref("");
const captchaError = ref("");
const loadingCaptcha = ref(false);

// 忘记密码相关
const showForgotPasswordModal = ref(false);
const forgotPasswordEmail = ref("");
const forgotPasswordLoading = ref(false);
const forgotPasswordSuccess = ref(false);
const resetPasswordToken = ref("");
const showResetPasswordModal = ref(false);
const resetPasswordData = ref({
  password: "",
  confirmPassword: "",
});
const resetPasswordLoading = ref(false);

// 表单数据
const formData = ref({
  name: "",
  email: "",
  password: "",
  confirmPassword: "",
});

// 验证状态
const nameError = ref("");
const emailError = ref("");
const passwordError = ref("");
const confirmPasswordError = ref("");

// Google OAuth Client ID
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

let googleSignInInstance: any = null;

// 显示 Toast 通知
const showToast = (type: "success" | "error" | "warning" | "info", title: string, message?: string) => {
  const event = new CustomEvent("show-toast", {
    detail: { type, title, message },
  });
  window.dispatchEvent(event);
};

// 验证函数
const validateName = () => {
  if (!isLogin.value) {
    const name = formData.value.name.trim();
    if (!name) {
      nameError.value = "";
      return false;
    }
    if (name.length < 2) {
      nameError.value = "用户名至少为2个字符";
      return false;
    }
    if (name.length > 50) {
      nameError.value = "用户名不能超过50个字符";
      return false;
    }
    nameError.value = "";
    return true;
  }
  return true;
};

const validateEmail = () => {
  const email = formData.value.email.trim();
  if (!email) {
    emailError.value = "";
    return false;
  }
  const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  if (!emailPattern.test(email)) {
    emailError.value = "请输入有效的邮箱地址";
    return false;
  }
  emailError.value = "";
  return true;
};

const validatePassword = () => {
  const password = formData.value.password;
  if (!password) {
    passwordError.value = "";
    return false;
  }
  if (!isLogin.value) {
    if (password.length < 8) {
      passwordError.value = "密码长度至少为8位";
      return false;
    }
    if (password.length > 128) {
      passwordError.value = "密码不能超过128个字符";
      return false;
    }
  }
  passwordError.value = "";
  return true;
};

const validateConfirmPassword = () => {
  if (!isLogin.value) {
    const password = formData.value.password;
    const confirmPassword = formData.value.confirmPassword;
    if (!confirmPassword) {
      confirmPasswordError.value = "";
      return false;
    }
    if (password !== confirmPassword) {
      confirmPasswordError.value = "两次输入的密码不一致";
      return false;
    }
    confirmPasswordError.value = "";
    return true;
  }
  return true;
};

// 计算属性
const nameValid = computed(() => !nameError.value && formData.value.name.trim().length >= 2);
const emailValid = computed(() => !emailError.value && formData.value.email.trim().length > 0);
const passwordValid = computed(() => {
  if (isLogin.value) {
    return !passwordError.value && formData.value.password.length > 0;
  }
  return !passwordError.value && formData.value.password.length >= 8;
});
const confirmPasswordValid = computed(() => {
  if (isLogin.value) return true;
  return !confirmPasswordError.value && formData.value.password === formData.value.confirmPassword && formData.value.confirmPassword.length > 0;
});

// 密码强度计算
const passwordStrength = computed(() => {
  const password = formData.value.password;
  if (!password || isLogin.value) return { level: 0, text: "" };
  
  let strength = 0;
  if (password.length >= 8) strength++;
  if (password.length >= 12) strength++;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
  if (/\d/.test(password)) strength++;
  if (/[^a-zA-Z0-9]/.test(password)) strength++;
  
  if (strength <= 2) return { level: 1, text: "弱" };
  if (strength <= 3) return { level: 2, text: "中" };
  return { level: 3, text: "强" };
});

const passwordStrengthClass = computed(() => {
  const level = passwordStrength.value.level;
  if (level === 1) return "weak";
  if (level === 2) return "medium";
  if (level === 3) return "strong";
  return "";
});

const passwordStrengthText = computed(() => {
  return passwordStrength.value.text;
});

// 表单验证
const isFormValid = computed(() => {
  if (isLogin.value) {
    return emailValid.value && passwordValid.value;
  }
  return nameValid.value && emailValid.value && passwordValid.value && confirmPasswordValid.value;
});

// 加载验证码
const loadCaptcha = async () => {
  loadingCaptcha.value = true;
  captchaError.value = "";
  try {
    const result = await getCaptcha();
    captchaImage.value = result.image;
    captchaSession.value = result.session_id;
    captchaCode.value = "";
  } catch (err: any) {
    captchaError.value = err.message || "获取验证码失败";
    showToast("error", "验证码加载失败", err.message);
  } finally {
    loadingCaptcha.value = false;
  }
};

// 忘记密码
const handleForgotPassword = async () => {
  if (!forgotPasswordEmail.value.trim()) {
    showToast("error", "请输入邮箱地址");
    return;
  }
  if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(forgotPasswordEmail.value.trim())) {
    showToast("error", "请输入有效的邮箱地址");
    return;
  }
  
  forgotPasswordLoading.value = true;
  try {
    const result = await forgotPassword({ email: forgotPasswordEmail.value.trim() });
    forgotPasswordSuccess.value = true;
    // 开发环境显示重置链接
    if (result.reset_url) {
      showToast("info", "开发环境提示", `重置链接：${result.reset_url}`);
    } else {
      showToast("success", "邮件已发送", result.message);
    }
  } catch (err: any) {
    showToast("error", "请求失败", err.message);
  } finally {
    forgotPasswordLoading.value = false;
  }
};

// 重置密码
const handleResetPassword = async () => {
  if (!resetPasswordData.value.password) {
    showToast("error", "请输入新密码");
    return;
  }
  if (resetPasswordData.value.password.length < 8) {
    showToast("error", "密码长度至少为8位");
    return;
  }
  if (resetPasswordData.value.password !== resetPasswordData.value.confirmPassword) {
    showToast("error", "两次输入的密码不一致");
    return;
  }
  
  resetPasswordLoading.value = true;
  try {
    await resetPassword({
      token: resetPasswordToken.value,
      new_password: resetPasswordData.value.password,
    });
    showToast("success", "密码重置成功", "请使用新密码登录");
    showResetPasswordModal.value = false;
    resetPasswordData.value = { password: "", confirmPassword: "" };
    // 切换到登录模式
    isLogin.value = true;
  } catch (err: any) {
    showToast("error", "重置失败", err.message);
  } finally {
    resetPasswordLoading.value = false;
  }
};

onMounted(() => {
  // 检查URL中是否有重置密码token
  if (typeof window !== "undefined") {
    const url = new URL(window.location.href);
    const token = url.searchParams.get("token");
    if (token) {
      resetPasswordToken.value = token;
      showResetPasswordModal.value = true;
      // 清理URL
      url.searchParams.delete("token");
      window.history.replaceState({}, "", url.toString());
    }
  }
  
  // 处理 GitHub OAuth 回跳
  if (typeof window !== "undefined") {
    try {
      const url = new URL(window.location.href);
      const authToken = url.searchParams.get("auth_token");
      const userB64 = url.searchParams.get("user");
      const provider = url.searchParams.get("provider");
      if (provider === "github" && authToken && userB64) {
        const userJson = decodeURIComponent(escape(atob(userB64)));
        const user = JSON.parse(userJson);
        userStore.login(user, authToken);

        // 清理 URL
        url.searchParams.delete("auth_token");
        url.searchParams.delete("user");
        url.searchParams.delete("provider");
        window.history.replaceState({}, "", url.toString());

        const redirect = (url.searchParams.get("redirect") || (router.currentRoute.value.query.redirect as string) || "/") as string;
        showToast("success", "登录成功", "欢迎回来！");
        router.push(redirect);
        return;
      }
    } catch (e) {
      console.warn("Failed to parse github auth callback params", e);
    }
  }

  if (GOOGLE_CLIENT_ID && typeof window !== "undefined" && (window as any).google) {
    initializeGoogleSignIn();
  } else if (GOOGLE_CLIENT_ID) {
    const checkGoogle = setInterval(() => {
      if ((window as any).google) {
        clearInterval(checkGoogle);
        initializeGoogleSignIn();
      }
    }, 100);
    
    setTimeout(() => {
      clearInterval(checkGoogle);
    }, 10000);
  }
  
  // 加载验证码
  loadCaptcha();
});

onUnmounted(() => {
  if (googleSignInInstance) {
    googleSignInInstance.abort();
  }
});

const initializeGoogleSignIn = () => {
  if (!GOOGLE_CLIENT_ID || !(window as any).google) return;
  
  try {
    (window as any).google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: handleGoogleCredentialResponse,
    });
  } catch (err) {
    console.error("Failed to initialize Google Sign-In:", err);
  }
};

const handleGoogleCredentialResponse = async (response: { credential: string }) => {
  loading.value = true;
  error.value = "";

  try {
    const result = await googleLogin(response.credential);
    userStore.login(result.user, result.token, rememberMe.value);
    const redirect = router.currentRoute.value.query.redirect as string || "/";
    showToast("success", "登录成功", `欢迎回来，${result.user.name || result.user.email}！`);
    router.push(redirect);
  } catch (err: any) {
    console.error("Google login error:", err);
    let errorMessage = "Google登录失败，请稍后重试";
    if (err.message) {
      try {
        const errorData = JSON.parse(err.message);
        errorMessage = errorData.detail || errorMessage;
      } catch {
        errorMessage = err.message;
      }
    }
    error.value = errorMessage;
    showToast("error", "登录失败", errorMessage);
  } finally {
    loading.value = false;
  }
};

const toggleMode = () => {
  isLogin.value = !isLogin.value;
  error.value = "";
  nameError.value = "";
  emailError.value = "";
  passwordError.value = "";
  confirmPasswordError.value = "";
  captchaError.value = "";
  captchaCode.value = "";
  formData.value = {
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  };
  // 切换模式时保持记住我状态
  // 切换模式时重新加载验证码
  if (!isLogin.value) {
    loadCaptcha();
  } else {
    // 登录时也加载验证码
    loadCaptcha();
  }
};

const handleSubmit = async () => {
  error.value = "";
  
  // 验证所有字段
  const nameOk = isLogin.value || validateName();
  const emailOk = validateEmail();
  const passwordOk = validatePassword();
  const confirmPasswordOk = isLogin.value || validateConfirmPassword();
  
  if (!nameOk || !emailOk || !passwordOk || !confirmPasswordOk) {
    error.value = "请检查并修正表单错误";
    return;
  }
  
  if (!isLogin.value) {
    if (formData.value.password !== formData.value.confirmPassword) {
      error.value = "两次输入的密码不一致";
      return;
    }
    if (formData.value.password.length < 8) {
      error.value = "密码长度至少为8位";
      return;
    }
  }

  loading.value = true;

  try {
    if (isLogin.value) {
      // 邮箱登录
      const result = await emailLogin({
        email: formData.value.email.trim(),
        password: formData.value.password,
        captcha_code: captchaCode.value.trim(),
        captcha_session: captchaSession.value,
      });
      userStore.login(result.user, result.token, rememberMe.value);
      showToast("success", "登录成功", `欢迎回来，${result.user.name || result.user.email}！`);
    } else {
      // 邮箱注册
      const result = await emailRegister({
        name: formData.value.name.trim(),
        email: formData.value.email.trim(),
        password: formData.value.password,
        captcha_code: captchaCode.value.trim(),
        captcha_session: captchaSession.value,
      });
      userStore.login(result.user, result.token, true); // 注册时默认记住
      showToast("success", "注册成功", `账户创建成功，欢迎使用，${result.user.name}！`);
    }

    // 跳转到首页或之前的页面
    const redirect = router.currentRoute.value.query.redirect as string || "/";
    router.push(redirect);
  } catch (err: any) {
    console.error("Auth error:", err);
    const errorMessage = err.message || (isLogin.value ? "登录失败，请检查邮箱和密码" : "注册失败，请稍后重试");
    error.value = errorMessage;
    showToast("error", isLogin.value ? "登录失败" : "注册失败", errorMessage);
  } finally {
    loading.value = false;
  }
};

const handleSocialLogin = async (provider: "google" | "github") => {
  if (provider === "google") {
    if (!GOOGLE_CLIENT_ID) {
      showToast("error", "配置错误", "Google OAuth未配置，请联系管理员");
      return;
    }

    if (!(window as any).google) {
      showToast("error", "服务错误", "Google登录服务加载失败，请刷新页面重试");
      return;
    }

    loading.value = true;
    error.value = "";

    try {
      const buttonContainer = document.createElement('div');
      buttonContainer.style.position = 'fixed';
      buttonContainer.style.left = '-9999px';
      buttonContainer.style.top = '-9999px';
      document.body.appendChild(buttonContainer);
      
      (window as any).google.accounts.id.renderButton(
        buttonContainer,
        {
          theme: 'outline',
          size: 'large',
          type: 'standard',
          text: 'signin_with',
          shape: 'rectangular',
          logo_alignment: 'left',
        }
      );
      
      setTimeout(() => {
        const button = buttonContainer.querySelector('div[role="button"]') as HTMLElement;
        if (button) {
          button.click();
        } else {
          setTimeout(() => {
            const retryButton = buttonContainer.querySelector('div[role="button"]') as HTMLElement;
            if (retryButton) {
              retryButton.click();
            } else {
              loading.value = false;
              showToast("error", "登录失败", "无法启动Google登录，请刷新页面重试");
            }
          }, 500);
        }
        setTimeout(() => {
          if (document.body.contains(buttonContainer)) {
            document.body.removeChild(buttonContainer);
          }
        }, 2000);
      }, 200);
    } catch (err: any) {
      error.value = "Google登录失败，请稍后重试";
      console.error("Google login error:", err);
      loading.value = false;
      showToast("error", "登录失败", "Google登录失败，请稍后重试");
    }
  } else if (provider === "github") {
    const redirect = (router.currentRoute.value.query.redirect as string) || "/";
    const url = new URL(`${API_BASE}/auth/github/start`);
    url.searchParams.set("redirect", redirect);
    window.location.href = url.toString();
  }
};
</script>
