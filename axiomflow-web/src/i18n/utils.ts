import type { Composer } from "vue-i18n";

export function formatNumber(locale: string, value: number, options?: Intl.NumberFormatOptions) {
  try {
    return new Intl.NumberFormat(locale, options).format(value);
  } catch {
    return String(value);
  }
}

export function formatDateTime(locale: string, timeStr: string, options?: Intl.DateTimeFormatOptions) {
  if (!timeStr) return "";
  try {
    const date = new Date(timeStr);
    if (!Number.isFinite(date.getTime())) return timeStr;
    return new Intl.DateTimeFormat(locale, {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      ...options,
    }).format(date);
  } catch {
    return timeStr;
  }
}

export function formatRelativeTime(t: Composer["t"], locale: string, timeStr: string) {
  if (!timeStr) return t("common.unknown");
  const ts = new Date(timeStr).getTime();
  if (!Number.isFinite(ts)) return timeStr;

  const diff = Date.now() - ts;
  if (diff < 0) return t("time.justNow");

  const sec = Math.floor(diff / 1000);
  if (sec < 60) return t("time.justNow");

  const min = Math.floor(sec / 60);
  if (min < 60) return t("time.minutesAgo", { count: min });

  const hr = Math.floor(min / 60);
  if (hr < 24) return t("time.hoursAgo", { count: hr });

  const day = Math.floor(hr / 24);
  if (day < 7) return t("time.daysAgo", { count: day });

  return formatDateTime(locale, timeStr);
}


