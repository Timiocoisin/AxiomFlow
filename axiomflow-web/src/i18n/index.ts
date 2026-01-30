import { createI18n } from 'vue-i18n';
import zhCN from './locales/zh-CN.json';
import zhTW from './locales/zh-TW.json';
import enUS from './locales/en-US.json';
import jaJP from './locales/ja-JP.json';
import koKR from './locales/ko-KR.json';
import frFR from './locales/fr-FR.json';
import deDE from './locales/de-DE.json';
import esES from './locales/es-ES.json';

// 支持的语言列表
export type SupportedLocale = 'zh-CN' | 'zh-TW' | 'en-US' | 'ja-JP' | 'ko-KR' | 'fr-FR' | 'de-DE' | 'es-ES';

export const supportedLocales: SupportedLocale[] = [
  'zh-CN',
  'zh-TW',
  'en-US',
  'ja-JP',
  'ko-KR',
  'fr-FR',
  'de-DE',
  'es-ES',
];

// 语言映射表（用于自动检测）
const localeMap: Record<string, SupportedLocale> = {
  'zh': 'zh-CN',
  'zh-CN': 'zh-CN',
  'zh-TW': 'zh-TW',
  'zh-HK': 'zh-TW',
  'en': 'en-US',
  'en-US': 'en-US',
  'ja': 'ja-JP',
  'ja-JP': 'ja-JP',
  'ko': 'ko-KR',
  'ko-KR': 'ko-KR',
  'fr': 'fr-FR',
  'fr-FR': 'fr-FR',
  'de': 'de-DE',
  'de-DE': 'de-DE',
  'es': 'es-ES',
  'es-ES': 'es-ES',
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
    'ja-JP': jaJP,
    'ko-KR': koKR,
    'fr-FR': frFR,
    'de-DE': deDE,
    'es-ES': esES,
  },
});

export default i18n;

