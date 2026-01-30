<template>
  <div class="app-shell">
    <header class="app-header">
      <button
        class="logo"
        type="button"
        :title="$t('app.title')"
        @click="router.push('/')"
      >
        <img src="/icons/favicon.svg" alt="AxiomFlow" class="logo-image" />
        <span class="logo-text">
          AxiomFlow
          <span class="logo-badge">Beta</span>
        </span>
      </button>
      <button
        class="nav-toggle"
        type="button"
        :aria-label="isNavOpen ? $t('nav.closeNavMenu') : $t('nav.openNavMenu')"
        :aria-expanded="isNavOpen"
        @click="isNavOpen = !isNavOpen"
      >
        <span class="nav-toggle-line"></span>
        <span class="nav-toggle-line"></span>
        <span class="nav-toggle-line"></span>
      </button>
      <nav class="nav-links" :class="{ 'nav-links-open': isNavOpen }">
        <RouterLink
          to="/"
          class="nav-link-item"
          active-class=""
          exact-active-class="router-link-active"
          @click="isNavOpen = false"
        >
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 9L12 2L21 9V20C21 20.5304 20.7893 21.0391 20.4142 21.4142C20.0391 21.7893 19.5304 22 19 22H5C4.46957 22 3.96086 21.7893 3.58579 21.4142C3.21071 21.0391 3 20.5304 3 20V9Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M9 22V12H15V22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>{{ $t('nav.home') }}</span>
        </RouterLink>
        <RouterLink 
          to="/app" 
          class="nav-link-item"
          active-class=""
          exact-active-class="router-link-active"
          @click="isNavOpen = false"
        >
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M14 2V8H20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M16 13H8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M16 17H8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M10 9H9H8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>{{ $t('nav.documents') }}</span>
        </RouterLink>
        <button
          v-if="!userStore.isLoggedIn"
          class="user-avatar-button login-button"
          @click="goToLogin"
          :title="$t('nav.login')"
        >
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="login-text">{{ $t('nav.login') }}</span>
        </button>
        <div
          v-else
          class="user-menu-wrapper"
          @mouseenter="showMenu = true"
          @mouseleave="showMenu = false"
          @focusin="showMenu = true"
          @focusout="handleMenuFocusOut"
        >
          <button 
            class="user-avatar-button" 
            :class="{ 'has-avatar': userStore.user?.avatar }"
            :aria-label="showMenu ? $t('nav.closeAccountMenu') : $t('nav.openAccountMenu')"
            :aria-expanded="showMenu"
            aria-haspopup="true"
            :title="$t('nav.accountMenu')"
            @click="showMenu = !showMenu"
            @keydown.enter="showMenu = !showMenu"
            @keydown.space.prevent="showMenu = !showMenu"
          >
            <img
              v-if="userStore.user?.avatar"
              :src="userStore.user.avatar"
              :alt="userStore.user?.name || 'User'"
              class="user-avatar-image"
              @error="handleAvatarError"
              @load="handleAvatarLoad"
            />
            <span v-else class="user-avatar-text">{{ userStore.user?.name?.charAt(0).toUpperCase() || 'U' }}</span>
          </button>
          <Transition name="user-menu-fade">
          <div v-if="showMenu" class="user-menu">
            <div class="user-menu-header">
              <div class="user-menu-avatar">
                <img
                  v-if="userStore.user?.avatar"
                  :src="userStore.user.avatar"
                  :alt="userStore.user?.name || 'User'"
                  class="user-menu-avatar-image"
                  @error="handleAvatarError"
                  @load="handleAvatarLoad"
                />
                <span v-else>{{ userStore.user?.name?.charAt(0).toUpperCase() || 'U' }}</span>
              </div>
              <div class="user-menu-info">
                <div class="user-menu-name">{{ userStore.user?.name || $t('nav.user') }}</div>
                <div class="user-menu-email">
                  {{ userStore.user?.email }}
                </div>
              </div>
            </div>
            <div class="user-menu-divider"></div>
            <button class="user-menu-item" @click="goToProfile">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>{{ $t('nav.profile') }}</span>
            </button>
            <button class="user-menu-item" @click="goToHelp">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 9C9.27251 8.33167 9.73144 7.76811 10.307 7.40937C10.8826 7.05064 11.5444 6.91509 12.1979 7.02185C12.8514 7.12861 13.4587 7.47176 13.9142 8.00001C14.3697 8.52826 14.6447 9.20757 14.695 9.92334C14.7453 10.6391 14.567 11.3517 14.1875 11.9444C13.808 12.5371 13.2474 12.9789 12.6 13.2V14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 17H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>{{ $t('nav.help') }}</span>
            </button>
            <div class="user-menu-divider"></div>
            <div class="user-menu-item language-selector">
              <button
                class="language-selector-button"
                type="button"
                :aria-label="$t('nav.language')"
                aria-haspopup="listbox"
                :aria-expanded="showLanguageMenu"
                @click.stop="showLanguageMenu = !showLanguageMenu"
                @keydown.down.prevent="openLanguageMenuAndMove(1)"
                @keydown.up.prevent="openLanguageMenuAndMove(-1)"
                @keydown.enter.prevent="showLanguageMenu = !showLanguageMenu"
                @keydown.space.prevent="showLanguageMenu = !showLanguageMenu"
                @keydown.esc.prevent="showLanguageMenu = false"
              >
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 5h16M4 12h9M4 19h6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M15 19l2-6 2 6m-3-2h2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
                <span>{{ $t('language.label', { lang: currentLanguageLabel }) }}</span>
                <svg class="language-arrow" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
              <Transition name="language-menu-fade">
                <div
                  v-if="showLanguageMenu"
                  class="language-menu"
                  role="listbox"
                  tabindex="-1"
                  @keydown.down.prevent="moveLanguageSelection(1)"
                  @keydown.up.prevent="moveLanguageSelection(-1)"
                  @keydown.enter.prevent="selectActiveLanguage()"
                  @keydown.esc.prevent="showLanguageMenu = false"
                >
                  <button
                    v-for="option in languageOptions"
                    :key="option.value"
                    class="language-menu-item"
                    type="button"
                    role="option"
                    :aria-selected="locale === option.value"
                    :class="{ 'active': locale === option.value }"
                    @click="selectLanguage(option.value)"
                  >
                    <span>{{ option.label }}</span>
                    <svg v-if="locale === option.value" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
            </button>
                </div>
              </Transition>
            </div>
            <div class="user-menu-divider"></div>
            <button class="user-menu-item" @click="goToSettings">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 15C13.6569 15 15 13.6569 15 12C15 10.3431 13.6569 9 12 9C10.3431 9 9 10.3431 9 12C9 13.6569 10.3431 15 12 15Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M19.4 15C19.2669 15.3016 19.2272 15.6362 19.286 15.9606C19.3448 16.285 19.4995 16.5843 19.73 16.82L19.79 16.88C19.976 17.0657 20.1235 17.2863 20.2241 17.5291C20.3248 17.7719 20.3766 18.0322 20.3766 18.295C20.3766 18.5578 20.3248 18.8181 20.2241 19.0609C20.1235 19.3037 19.976 19.5243 19.79 19.71C19.6043 19.896 19.3837 20.0435 19.1409 20.1441C18.8981 20.2448 18.6378 20.2966 18.375 20.2966C18.1122 20.2966 17.8519 20.2448 17.6091 20.1441C17.3663 20.0435 17.1457 19.896 16.96 19.71L16.9 19.65C16.6643 19.4195 16.365 19.2648 16.0406 19.206C15.7162 19.1472 15.3816 19.1869 15.08 19.32C14.7842 19.4468 14.532 19.6572 14.3543 19.9255C14.1766 20.1938 14.0813 20.5082 14.08 20.83V21C14.08 21.5304 13.8693 22.0391 13.4942 22.4142C13.1191 22.7893 12.6104 23 12.08 23C11.5496 23 11.0409 22.7893 10.6658 22.4142C10.2907 22.0391 10.08 21.5304 10.08 21V20.91C10.0723 20.579 9.96512 20.258 9.77251 19.9887C9.5799 19.7194 9.31074 19.5143 9 19.4C8.69838 19.2669 8.36381 19.2272 8.03941 19.286C7.71502 19.3448 7.41568 19.4995 7.18 19.73L7.12 19.79C6.93425 19.976 6.71368 20.1235 6.47088 20.2241C6.22808 20.3248 5.96783 20.3766 5.705 20.3766C5.44217 20.3766 5.18192 20.3248 4.93912 20.2241C4.69632 20.1235 4.47575 19.976 4.29 19.79C4.10405 19.6043 3.95653 19.3837 3.85588 19.1409C3.75523 18.8981 3.70343 18.6378 3.70343 18.375C3.70343 18.1122 3.75523 17.8519 3.85588 17.6091C3.95653 17.3663 4.10405 17.1457 4.29 16.96L4.35 16.9C4.58054 16.6643 4.73519 16.365 4.794 16.0406C4.85282 15.7162 4.81312 15.3816 4.68 15.08C4.55324 14.7842 4.34276 14.532 4.07447 14.3543C3.80618 14.1766 3.49179 14.0813 3.17 14.08H3C2.46957 14.08 1.96086 13.8693 1.58579 13.4942C1.21071 13.1191 1 12.6104 1 12.08C1 11.5496 1.21071 11.0409 1.58579 10.6658C1.96086 10.2907 2.46957 10.08 3 10.08H3.09C3.42099 10.0723 3.742 9.96512 4.01131 9.77251C4.28062 9.5799 4.48568 9.31074 4.6 9C4.73312 8.69838 4.77282 8.36381 4.714 8.03941C4.65519 7.71502 4.50054 7.41568 4.27 7.18L4.21 7.12C4.02405 6.93425 3.87653 6.71368 3.77588 6.47088C3.67523 6.22808 3.62343 5.96783 3.62343 5.705C3.62343 5.44217 3.67523 5.18192 3.77588 4.93912C3.87653 4.69632 4.02405 4.47575 4.21 4.29C4.39575 4.10405 4.61632 3.95653 4.85912 3.85588C5.10192 3.75523 5.36217 3.70343 5.625 3.70343C5.88783 3.70343 6.14808 3.75523 6.39088 3.85588C6.63368 3.95653 6.85425 4.10405 7.04 4.29L7.1 4.35C7.33568 4.58054 7.63502 4.73519 7.95941 4.794C8.28381 4.85282 8.61838 4.81312 8.92 4.68H9C9.29577 4.55324 9.54802 4.34276 9.72569 4.07447C9.90337 3.80618 9.99872 3.49179 10 3.17V3C10 2.46957 10.2107 1.96086 10.5858 1.58579C10.9609 1.21071 11.4696 1 12 1C12.5304 1 13.0391 1.21071 13.4142 1.58579C13.7893 1.96086 14 2.46957 14 3V3.09C14.0013 3.41179 14.0966 3.72618 14.2743 3.99447C14.452 4.26276 14.7042 4.47324 15 4.6C15.3016 4.73312 15.6362 4.77282 15.9606 4.714C16.285 4.65519 16.5843 4.50054 16.82 4.27L16.88 4.21C17.0657 4.02405 17.2863 3.87653 17.5291 3.77588C17.7719 3.67523 18.0322 3.62343 18.295 3.62343C18.5578 3.62343 18.8181 3.67523 19.0609 3.77588C19.3037 3.87653 19.5243 4.02405 19.71 4.21C19.896 4.39575 20.0435 4.61632 20.1441 4.85912C20.2448 5.10192 20.2966 5.36217 20.2966 5.625C20.2966 5.88783 20.2448 6.14808 20.1441 6.39088C20.0435 6.63368 19.896 6.85425 19.71 7.04L19.65 7.1C19.4195 7.33568 19.2648 7.63502 19.206 7.95941C19.1472 8.28381 19.1869 8.61838 19.32 8.92V9C19.4468 9.29577 19.6572 9.54802 19.9255 9.72569C20.1938 9.90337 20.5082 9.99872 20.83 10H21C21.5304 10 22.0391 10.2107 22.4142 10.5858C22.7893 10.9609 23 11.4696 23 12C23 12.5304 22.7893 13.0391 22.4142 13.4142C22.0391 13.7893 21.5304 14 21 14H20.91C20.5882 14.0013 20.2738 14.0966 20.0055 14.2743C19.7372 14.452 19.5268 14.7042 19.4 15Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>{{ $t('nav.settings') }}</span>
            </button>
            <div class="user-menu-divider"></div>
            <button class="user-menu-item" @click="handleLogout">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M16 17L21 12L16 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M21 12H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>{{ $t('nav.logout') }}</span>
            </button>
          </div>
          </Transition>
        </div>
      </nav>
    </header>
    <div v-if="isRouteLoading" class="route-progress-bar"></div>
    <main class="app-main" :class="{ 'landing-page': isLandingPage, scrollable: isSettingsPage }">
      <RouterView />
    </main>
    <Toast />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, nextTick, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { supportedLocales, type SupportedLocale } from "@/i18n";
import { useUserStore } from "@/stores/user";
import Toast from "@/components/Toast.vue";

const route = useRoute();
const router = useRouter();
const { t, locale } = useI18n();
const userStore = useUserStore();
const isLandingPage = computed(() => route.path === "/");
const isSettingsPage = computed(() => route.path === "/settings" || route.path.startsWith("/settings/"));
const showMenu = ref(false);
const isRouteLoading = ref(false);
const isNavOpen = ref(false);
const showLanguageMenu = ref(false);
const activeLanguageIndex = ref(0);

const currentLanguageLabel = computed(() => {
  const currentLocale = locale.value as SupportedLocale;
  const localeMap: Record<SupportedLocale, string> = {
    'zh-CN': t("language.zhCN"),
    'zh-TW': t("language.zhTW"),
    'en-US': t("language.enUS"),
    'ja-JP': t("language.jaJP"),
    'ko-KR': t("language.koKR"),
    'fr-FR': t("language.frFR"),
    'de-DE': t("language.deDE"),
    'es-ES': t("language.esES"),
  };
  return localeMap[currentLocale] || t("language.enUS");
});

// 获取所有支持的语言选项
const languageOptions = computed(() => {
  return supportedLocales.map(loc => ({
    value: loc,
    label: getLanguageLabel(loc),
  }));
});

watch([showLanguageMenu, locale], () => {
  if (!showLanguageMenu.value) return;
  const idx = languageOptions.value.findIndex((o) => o.value === (locale.value as SupportedLocale));
  activeLanguageIndex.value = idx >= 0 ? idx : 0;
});

const getLanguageLabel = (loc: SupportedLocale): string => {
  const localeMap: Record<SupportedLocale, string> = {
    'zh-CN': t("language.zhCN"),
    'zh-TW': t("language.zhTW"),
    'en-US': t("language.enUS"),
    'ja-JP': t("language.jaJP"),
    'ko-KR': t("language.koKR"),
    'fr-FR': t("language.frFR"),
    'de-DE': t("language.deDE"),
    'es-ES': t("language.esES"),
  };
  return localeMap[loc] || loc;
};

// 高优先级：修复缺失的头像处理方法
const handleAvatarError = (e: Event) => {
  const img = e.target as HTMLImageElement;
  // 隐藏加载失败的图片，显示默认头像文字
  img.style.display = 'none';
  // 可以在这里添加错误日志记录
  console.debug('Avatar image failed to load:', img.src);
};

const handleAvatarLoad = (e: Event) => {
  const img = e.target as HTMLImageElement;
  // 确保图片正常显示
  img.style.display = 'block';
};

const goToLogin = () => {
  const redirect = route.path === "/" ? "/" : route.fullPath;
  router.push(`/auth?redirect=${encodeURIComponent(redirect)}`);
};

const handleLogout = () => {
  userStore.logout();
  showMenu.value = false;
  // 退出后回到登录页
  router.replace("/auth?redirect=/");
};

const goToProfile = () => {
  showMenu.value = false;
  // 这里暂时跳到设置页中的个人资料区域，后续可以替换为单独的 /profile 路由
  router.push("/settings?tab=profile");
};

const goToHelp = () => {
  showMenu.value = false;
  // 这里暂时跳到设置页中的帮助 / 反馈区域，后续可以替换为单独的 /help 路由
  router.push("/settings?tab=help");
};

const goToSettings = () => {
  showMenu.value = false;
  router.push("/settings");
};

const applyLanguage = (value: SupportedLocale) => {
  locale.value = value;
  localStorage.setItem("language", value);
};

const selectLanguage = (newLocale: SupportedLocale) => {
  if (locale.value === newLocale) {
    showLanguageMenu.value = false;
    return;
  }
  applyLanguage(newLocale);
  showLanguageMenu.value = false;
  // 添加语言切换反馈
  if (typeof window !== 'undefined' && (window as any).showToast) {
    (window as any).showToast({
      type: 'success',
      title: t("language.switchedTo", { 
        lang: getLanguageLabel(newLocale)
      }),
      duration: 2000,
    });
  }
};

const moveLanguageSelection = (delta: number) => {
  const n = languageOptions.value.length;
  if (n <= 0) return;
  activeLanguageIndex.value = (activeLanguageIndex.value + delta + n) % n;
};

const openLanguageMenuAndMove = (delta: number) => {
  if (!showLanguageMenu.value) {
    showLanguageMenu.value = true;
    nextTick(() => moveLanguageSelection(delta));
  } else {
    moveLanguageSelection(delta);
  }
};

const selectActiveLanguage = () => {
  const opt = languageOptions.value[activeLanguageIndex.value];
  if (!opt) return;
  selectLanguage(opt.value);
};


const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as HTMLElement;
  // 用户菜单点击外部关闭
  if (!target.closest(".user-menu-wrapper")) {
    showMenu.value = false;
  }
  // 语言菜单点击外部关闭
  if (!target.closest(".language-selector")) {
    showLanguageMenu.value = false;
  }
  // 中优先级：移动端菜单点击外部关闭
  if (!target.closest(".nav-links") && !target.closest(".nav-toggle")) {
    isNavOpen.value = false;
  }
};

// 中优先级：键盘导航支持
const handleKeydown = (e: KeyboardEvent) => {
  // ESC 键关闭菜单
  if (e.key === 'Escape') {
    if (showMenu.value) {
      showMenu.value = false;
      // 将焦点返回到触发按钮
      nextTick(() => {
        const avatarButton = document.querySelector('.user-avatar-button') as HTMLElement;
        avatarButton?.focus();
      });
    }
    if (isNavOpen.value) {
      isNavOpen.value = false;
      // 将焦点返回到切换按钮
      nextTick(() => {
        const navToggle = document.querySelector('.nav-toggle') as HTMLElement;
        navToggle?.focus();
      });
    }
    if (showLanguageMenu.value) {
      showLanguageMenu.value = false;
    }
  }
};

// 处理用户菜单焦点移出事件
const handleMenuFocusOut = (e: FocusEvent) => {
  const target = e.currentTarget as HTMLElement;
  const relatedTarget = e.relatedTarget as Node | null;
  // 如果焦点移出整个菜单区域，关闭菜单
  if (relatedTarget && !target.contains(relatedTarget)) {
    showMenu.value = false;
  }
};

let removeBeforeGuard: (() => void) | null = null;
let removeAfterGuard: (() => void) | null = null;

// 中优先级：路由切换时关闭移动端菜单
watch(() => route.path, () => {
  isNavOpen.value = false;
});

onMounted(() => {
  document.addEventListener("click", handleClickOutside);
  document.addEventListener("keydown", handleKeydown);
  userStore.loadUserFromStorage();

  // 语言设置已在 i18n/index.ts 中自动处理（包括自动检测和从 localStorage 读取）
  // 这里只需要同步到 localStorage（如果 i18n 初始化时没有读取到）
  const storedLang = localStorage.getItem("language") as SupportedLocale | null;
  if (storedLang && supportedLocales.includes(storedLang)) {
    locale.value = storedLang;
  } else {
    // 如果没有存储的语言，保存当前 i18n 检测到的语言
    localStorage.setItem("language", locale.value as string);
  }

  // 路由切换进度条
  removeBeforeGuard = router.beforeEach((to, from, next) => {
    if (to.path !== from.path) {
      isRouteLoading.value = true;
    }
    next();
  });

  removeAfterGuard = router.afterEach(() => {
    // 略微延迟，避免闪烁
    setTimeout(() => {
      isRouteLoading.value = false;
    }, 200);
  });
});

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside);
  document.removeEventListener("keydown", handleKeydown);
  if (removeBeforeGuard) removeBeforeGuard();
  if (removeAfterGuard) removeAfterGuard();
});

// 根据路由动态设置 body 类名
watch(isLandingPage, (isLanding) => {
  if (isLanding) {
    document.body.classList.add("landing-page");
  } else {
    document.body.classList.remove("landing-page");
  }
}, { immediate: true });
</script>


