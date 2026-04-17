import { createI18n } from "vue-i18n";

import enUS from "./locales/en-US";
import zhCN from "./locales/zh-CN";

export type UiLocale = "zh-CN" | "en-US";

const STORAGE_KEY = "axiomflow:uiLanguage";

function normalizeLocale(v: unknown): UiLocale {
  return v === "en-US" ? "en-US" : "zh-CN";
}

export function getInitialLocale(): UiLocale {
  try {
    return normalizeLocale(localStorage.getItem(STORAGE_KEY));
  } catch {
    return "zh-CN";
  }
}

export const i18n = createI18n({
  legacy: false,
  locale: getInitialLocale(),
  fallbackLocale: "zh-CN",
  messages: {
    "zh-CN": zhCN,
    "en-US": enUS,
  },
});

export function getLocale(): UiLocale {
  return normalizeLocale(i18n.global.locale.value);
}

export function setLocale(locale: UiLocale) {
  i18n.global.locale.value = normalizeLocale(locale);
  try {
    localStorage.setItem(STORAGE_KEY, normalizeLocale(locale));
  } catch {
    // ignore
  }
}

