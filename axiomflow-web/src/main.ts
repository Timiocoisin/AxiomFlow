import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import { router } from "./router";
import { i18n } from "./i18n";

import "./styles.css";

// RTL 语言列表
const rtlLocales = ['ar', 'he', 'fa', 'ur'];

// 初始化主题（light / dark），基于 localStorage 或系统偏好
function initTheme() {
  try {
    const stored = localStorage.getItem("theme");
    let theme: "light" | "dark";

    if (stored === "light" || stored === "dark") {
      theme = stored;
    } else {
      const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)").matches;
      theme = prefersDark ? "dark" : "light";
    }

    const html = document.documentElement;
    if (theme === "dark") {
      html.setAttribute("data-theme", "dark");
    } else {
      html.removeAttribute("data-theme");
    }
  } catch {
    // 安全兜底：出错时保持默认浅色
  }
}

initTheme();

const app = createApp(App);

// 全局错误兜底：避免页面"白屏"但控制台才有报错的情况
app.config.errorHandler = (err, instance, info) => {
  // eslint-disable-next-line no-console
  console.error("[VueError]", info, err);
  try {
    const message = err instanceof Error ? err.message : String(err);
    const event = new CustomEvent("show-toast", {
      detail: { type: "error", title: i18n.global.t("app.error"), message },
    });
    window.dispatchEvent(event);
  } catch {
    // ignore
  }
};

// 必须先注册插件，然后才能使用
app.use(createPinia());
app.use(router);
app.use(i18n);

// 初始化 RTL 支持（必须在 i18n 注册之后）
function initRTL() {
  try {
    const locale = i18n.global.locale.value;
    const isRTL = rtlLocales.some(rtl => locale.toLowerCase().includes(rtl));
    const html = document.documentElement;
    if (isRTL) {
      html.setAttribute('dir', 'rtl');
    } else {
      html.setAttribute('dir', 'ltr');
    }
  } catch {
    // 安全兜底
  }
}

initRTL();

app.mount("#app");


