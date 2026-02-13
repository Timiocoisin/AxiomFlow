import { createI18n } from 'vue-i18n';
import zhCN from './locales/zh-CN.json';
import zhTW from './locales/zh-TW.json';
import enUS from './locales/en-US.json';

// 支持的语言列表（已精简为：简体中文、繁体中文、英文）
export type SupportedLocale = 'zh-CN' | 'zh-TW' | 'en-US';

export const supportedLocales: SupportedLocale[] = [
  'zh-CN',
  'zh-TW',
  'en-US',
];

// 语言映射表（用于自动检测，只保留到三种目标语言的映射）
const localeMap: Record<string, SupportedLocale> = {
  'zh': 'zh-CN',
  'zh-CN': 'zh-CN',
  'zh-TW': 'zh-TW',
  'zh-HK': 'zh-TW',
  'en': 'en-US',
  'en-US': 'en-US',
};

// 从 localStorage 读取保存的语言设置，如果没有则根据浏览器语言自动检测
const getDefaultLocale = (): SupportedLocale => {
  const stored = localStorage.getItem('language') as SupportedLocale | null;
  if (stored && supportedLocales.includes(stored)) {
    return stored;
  }
  
  // 自动检测浏览器语言
  const browserLang = (navigator.language || (navigator as any).userLanguage || '').toLowerCase();
  
  // 精确匹配
  if (localeMap[browserLang]) {
    return localeMap[browserLang];
  }
  
  // 前缀匹配（例如 zh-Hans-CN -> zh-CN）
  for (const [key, value] of Object.entries(localeMap)) {
    if (browserLang.startsWith(key)) {
      return value;
    }
  }
  
  // 默认返回简体中文
  return 'zh-CN';
};

export const i18n = createI18n({
  legacy: false, // 使用 Composition API 模式
  locale: getDefaultLocale(),
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'zh-TW': zhTW,
    'en-US': enUS,
  },
});

export default i18n;

